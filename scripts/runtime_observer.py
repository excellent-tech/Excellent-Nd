#!/usr/bin/env python3
"""Run Symphony and synchronize non-transient interruptions with a GitHub Issue."""

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

from repository_adapter import preflight as repository_preflight
from repository_adapter import split_repo
from repository_adapter import transition_event
from repository_config import (
    dispatch_gates,
    read_config,
    routing_name,
    status_authority,
    status_name,
    status_names,
)

SYMPHONY_ACK_FLAG = "--i-understand-that-this-will-be-running-without-the-usual-guardrails"
MARKER_FILENAME = ".excellent-nd/runtime-transition.json"
TRANSITION_PREFIX = "EXCELLENT_ND_TRANSITION="
TRANSITION_SCHEMA = "excellent-nd/runtime-transition@v1"
RECEIPT_SCHEMA = "excellent-nd/runtime-transition-receipt@v1"
TASK_SCHEMA = "excellent-nd/task@v1"
WORKER_START = re.compile(
    r"\bStarting worker attempt for issue_id=\S+ issue_identifier=GH-(\d+)\b"
)
SYMPHONY_LOG_SEGMENTS = 5
LOG_POLL_INTERVAL = 0.1
MAX_LOG_POLL_BYTES = 1024 * 1024
MAX_LOG_LINE_BYTES = 256 * 1024
RECENT_TRANSITION_KEYS = 4096


class LogFollowError(RuntimeError):
    """The authoritative Symphony log cannot be followed safely."""


class RecentKeys:
    """Bounded fingerprints for suppressing replayed lifecycle records."""

    def __init__(self, limit=RECENT_TRANSITION_KEYS):
        self.limit = limit
        self.order = deque()
        self.values = set()

    @staticmethod
    def _fingerprint(value):
        return hashlib.sha256(repr(value).encode("utf-8", errors="replace")).digest()

    def __contains__(self, value):
        return self._fingerprint(value) in self.values

    def add(self, value):
        fingerprint = self._fingerprint(value)
        if fingerprint in self.values:
            return
        if len(self.order) >= self.limit:
            self.values.remove(self.order.popleft())
        self.order.append(fingerprint)
        self.values.add(fingerprint)

    def __len__(self):
        return len(self.order)


class RotatingLogFollower:
    """Follow one active log plus numbered rotations without replaying startup data."""

    def __init__(self, base_path, missing_timeout=5.0, clock=time.monotonic):
        self.base_path = Path(base_path)
        self.missing_timeout = missing_timeout
        self.clock = clock
        self.started_at = clock()
        self.activity_seen = False
        self.last_bytes_read = 0
        self.last_referenced = set()
        self.streams = {}
        self._scan(initial=True)

    def _paths(self):
        return [self.base_path] + [
            Path(f"{self.base_path}.{number}")
            for number in range(1, SYMPHONY_LOG_SEGMENTS + 1)
        ]

    def _open(self, path, initial):
        try:
            stream = path.open("rb")
        except FileNotFoundError:
            return None
        except OSError as error:
            raise LogFollowError(f"authoritative Symphony log is unreadable: {error}") from error
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode):
            stream.close()
            raise LogFollowError("authoritative Symphony log is not a regular file")
        identity = (metadata.st_dev, metadata.st_ino)
        if identity in self.streams:
            stream.close()
            return identity
        if len(self.streams) >= (SYMPHONY_LOG_SEGMENTS + 1) * 2:
            stream.close()
            raise LogFollowError("too many rotating Symphony log inodes are active")
        offset = metadata.st_size if initial else 0
        stream.seek(offset)
        tail_size = min(offset, 64)
        tail = os.pread(stream.fileno(), tail_size, offset - tail_size) if tail_size else b""
        self.streams[identity] = {
            "stream": stream,
            "offset": offset,
            "known_size": metadata.st_size,
            "partial": b"",
            "tail": tail,
            "orphan_polls": 0,
        }
        return identity

    def _scan(self, initial=False):
        identities = set()
        for path in self._paths():
            try:
                metadata = path.stat()
            except FileNotFoundError:
                continue
            except OSError as error:
                raise LogFollowError(f"authoritative Symphony log is unavailable: {error}") from error
            if not stat.S_ISREG(metadata.st_mode):
                raise LogFollowError("authoritative Symphony log is not a regular file")
            identity = self._open(path, initial)
            if identity is not None:
                identities.add(identity)
        return identities

    @staticmethod
    def _read_bytes(stream, size):
        return stream.read(size)

    @staticmethod
    def _read(entry):
        stream = entry["stream"]
        metadata = os.fstat(stream.fileno())
        offset = entry["offset"]
        tail = entry["tail"]
        tail_offset = offset - len(tail)
        rewritten = metadata.st_size < offset or (
            tail and os.pread(stream.fileno(), len(tail), tail_offset) != tail
        )
        if rewritten:
            if offset < entry["known_size"]:
                raise LogFollowError(
                    "authoritative Symphony log was rewritten with unread data"
                )
            stream.seek(0)
            entry.update(offset=0, known_size=metadata.st_size, partial=b"", tail=b"")
            offset = 0
            tail = b""
            tail_offset = 0
        else:
            entry["known_size"] = max(entry["known_size"], metadata.st_size)

        lines = []
        bytes_read = 0
        backlog = metadata.st_size - offset
        if backlog > MAX_LOG_POLL_BYTES:
            raise LogFollowError("authoritative Symphony log exceeded maximum poll backlog")
        snapshot = os.pread(stream.fileno(), backlog, offset)
        if len(snapshot) != backlog:
            raise LogFollowError("authoritative Symphony log changed during read")
        snapshot_digest = hashlib.sha256(snapshot).digest()
        del snapshot
        chunk = RotatingLogFollower._read_bytes(stream, backlog)
        current_digest = hashlib.sha256(
            os.pread(stream.fileno(), backlog, offset)
        ).digest()
        if (
            len(chunk) != backlog
            or hashlib.sha256(chunk).digest() != snapshot_digest
            or current_digest != snapshot_digest
        ):
            raise LogFollowError("authoritative Symphony log changed during read")
        if chunk:
            bytes_read += len(chunk)
            entry["offset"] = stream.tell()
            entry["tail"] = (entry["tail"] + chunk)[-64:]
            parts = (entry["partial"] + chunk).split(b"\n")
            entry["partial"] = parts.pop()
            if len(entry["partial"]) > MAX_LOG_LINE_BYTES or any(
                len(part) > MAX_LOG_LINE_BYTES for part in parts
            ):
                raise LogFollowError("authoritative Symphony log exceeded maximum line size")
            lines.extend(part.rstrip(b"\r").decode("utf-8", errors="replace") for part in parts)
        return lines, bytes_read

    def poll(self):
        referenced = self._scan()
        lines = []
        self.last_bytes_read = 0

        bytes_by_identity = {}
        read_identities = set()

        def read(identity):
            entry = self.streams[identity]
            try:
                new_lines, bytes_read = self._read(entry)
                lines.extend(new_lines)
                self.last_bytes_read += bytes_read
                bytes_by_identity[identity] = bytes_read
                read_identities.add(identity)
                self.activity_seen = self.activity_seen or bytes_read > 0
            except OSError as error:
                raise LogFollowError(f"authoritative Symphony log follow failed: {error}") from error

        for identity in list(self.streams):
            read(identity)

        # A rotation can happen while the old descriptors are being drained.
        referenced = self._scan()
        for identity in referenced - read_identities:
            read(identity)
        self.last_referenced = referenced

        for identity, entry in list(self.streams.items()):
            if identity in referenced:
                entry["orphan_polls"] = 0
                continue
            if bytes_by_identity.get(identity, 0) > 0:
                entry["orphan_polls"] = 0
                continue
            entry["orphan_polls"] += 1
            if entry["orphan_polls"] < 2:
                continue
            if entry["partial"]:
                raise LogFollowError("rotated Symphony log ended with an incomplete line")
            entry["stream"].close()
            del self.streams[identity]

        if self.clock() - self.started_at >= self.missing_timeout:
            if not referenced and not self.streams:
                raise LogFollowError("authoritative Symphony log is unavailable")
            if not self.activity_seen:
                raise LogFollowError("authoritative Symphony log has no new activity")
        return lines

    def assert_available(self):
        if not self.activity_seen:
            raise LogFollowError("authoritative Symphony log has no new activity")
        if not self.last_referenced:
            raise LogFollowError("authoritative Symphony log is unavailable")

    def close(self):
        for entry in self.streams.values():
            entry["stream"].close()
        self.streams.clear()

BLOCKING_PATTERNS = (
    ("turn_timeout", re.compile(r"(turn timeout|turn timed out)", re.I)),
    ("app_server_startup", re.compile(r"(?=.*(?:thread/start|app[ -]?server|session (?:initialization|startup)))(?=.*(?:fail|error|exit|reject))", re.I)),
    ("agent_abnormal_exit", re.compile(r"(agent|subprocess).*(?:abnormal exit|crash|exited unexpectedly)", re.I)),
)


def classify_interruption(line):
    if re.search(r"(account usage|usage limit|weekly limit|quota exhausted)", line, re.I):
        return "usage_limit"
    if re.search(r"rate limit", line, re.I):
        retry = re.search(r"retry_after=(\d+)", line)
        if "reset_at=" in line or (retry and int(retry.group(1)) >= 3600):
            return "usage_limit"
    for category, pattern in BLOCKING_PATTERNS:
        if pattern.search(line):
            return category
    return None


def extract_context(line):
    def field(name, pattern=r"[A-Za-z0-9._:-]+"):
        match = re.search(rf"\b{name}=({pattern})", line)
        return match.group(1) if match else None
    issue = re.search(r"\bissue_identifier=GH-(\d+)\b", line)
    session = field("session_id")
    return {
        "issue_number": int(issue.group(1)) if issue else None,
        "session_id": None if session in (None, "n/a", "unknown") else session,
        "attempt": field("attempt", r"\d+"),
        "reset_at": field("reset_at"),
        "retry_after": field("retry_after", r"\d+"),
    }


def worker_started_issue(line):
    match = WORKER_START.search(line)
    return int(match.group(1)) if match else None


def encode_transition_event(event):
    payload = json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
    return TRANSITION_PREFIX + base64.urlsafe_b64encode(payload).decode()


def decode_transition_event(value):
    match = re.search(rf"{TRANSITION_PREFIX}([A-Za-z0-9_=-]+)", value)
    if not match:
        raise ValueError("structured transition marker is missing")
    try:
        return json.loads(base64.urlsafe_b64decode(match.group(1)).decode())
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("structured transition marker is invalid") from error


def sanitize(value):
    value = re.sub(r"https://[^/@\s]+:[^/@\s]+@", "https://[REDACTED]@", value)
    value = re.sub(r"\b(?:github_pat_|gh[pousr]_|sk-)[A-Za-z0-9_-]+", "[REDACTED]", value)
    value = re.sub(
        r"\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY)[A-Z0-9_]*)=\S+",
        r"\1=[REDACTED]", value, flags=re.I,
    )
    value = re.sub(r"(?:/home|/Users)/[^\s]+", "[PRIVATE_PATH]", value)
    value = re.sub(r"[A-Za-z]:\\Users\\[^\s]+", "[PRIVATE_PATH]", value)
    return value.replace(chr(96), "'")[:2000]


def set_workflow_status(body, status):
    updated, count = re.subn(
        r'("workflow_status"\s*:\s*")[^"]+(")', rf"\g<1>{status}\2", body
    )
    if count != 1:
        raise ValueError("Issue body must contain exactly one workflow_status field")
    return updated


def set_human_gate(body, value):
    updated, count = re.subn(
        r'("human_gate"\s*:\s*")[^"]+(")', rf"\g<1>{value}\2", body
    )
    if count > 1:
        raise ValueError("Issue body must contain at most one human_gate field")
    return updated


def task_control_metadata(body):
    candidates = []
    for match in re.finditer(r"\x60\x60\x60json\s*(\{.*?\})\s*\x60\x60\x60", body, re.S):
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("schema") == TASK_SCHEMA:
            candidates.append(value)
    if len(candidates) != 1:
        raise ValueError("Issue body must contain exactly one excellent-nd/task@v1 metadata block")
    return candidates[0]


def dependency_issue_numbers(metadata, repo):
    dependencies = metadata.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise ValueError("plan continuation requires at least one durable dependency")
    pattern = re.compile(
        rf"^https://github\.com/{re.escape(repo)}/issues/(\d+)$"
    )
    numbers = []
    for dependency in dependencies:
        if not isinstance(dependency, str):
            raise ValueError("plan continuation dependency is invalid")
        match = pattern.fullmatch(dependency)
        if not match:
            raise ValueError(
                "plan continuation requires same-repository GitHub Issue dependency URLs"
            )
        numbers.append(int(match.group(1)))
    return numbers


def validate_plan_continuation_issue(issue, repo, plan_ref, fetch_issue):
    if issue.get("state") != "open":
        raise ValueError("plan continuation requires an open Task Issue")
    metadata = task_control_metadata(issue.get("body") or "")
    if metadata.get("dispatch_scope", "task") != "plan":
        raise ValueError("Task is not authorized for Plan continuation")
    if metadata.get("human_gate", "clear") != "clear":
        raise ValueError("Task requires a fresh human decision before continuation")
    if metadata.get("plan_ref") != plan_ref:
        raise ValueError("Plan continuation reference does not match Task metadata")
    if metadata.get("workflow_status") not in ("blocked", "scheduled"):
        raise ValueError("Task workflow state is not eligible for Plan continuation")
    for number in dependency_issue_numbers(metadata, repo):
        dependency = fetch_issue(number)
        if dependency.get("state") != "closed":
            raise ValueError(f"dependency Issue #{number} is not closed")
    return metadata


def next_labels(labels, status, config):
    route = routing_name(config)
    if status_authority(config) == "github-project":
        kept = [label for label in labels if label != route]
        if status in ("scheduled", "running"):
            kept.append(route)
        return kept

    configured_statuses = status_names(config)
    kept = [label for label in labels if label != route and label not in configured_statuses]
    if status in ("scheduled", "running"):
        kept.append(route)
    kept.append(status_name(config, status))
    return kept


def runtime_event_for(status, block_kind):
    if status == "running":
        return "execution_started"
    if status == "review":
        return "review_ready"
    if status == "failed":
        return "execution_failed"
    if status == "blocked":
        return "decision_required" if block_kind == "decision" else "external_blocked"
    return None


class GitHub:
    def __init__(self, repo, config, token=None):
        split_repo(repo)
        self.repo = repo
        self.config = config
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN is required")

    def request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            f"https://api.github.com/repos/{self.repo}{path}",
            data=data, method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode(errors="replace")
            raise RuntimeError(f"GitHub API {error.code}: {sanitize(detail)}") from error

    def validate_plan_continuation(self, number, plan_ref):
        issue = self.request("GET", f"/issues/{number}")
        return validate_plan_continuation_issue(
            issue,
            self.repo,
            plan_ref,
            lambda dependency_number: self.request("GET", f"/issues/{dependency_number}"),
        )

    def transition(
        self,
        number,
        status,
        comment,
        block_kind="external",
        clear_human_gate=False,
    ):
        if status == "scheduled" and dispatch_gates(self.config):
            check = repository_preflight(self.repo, number, self.config)
            if check["result"] != "PASS":
                raise RuntimeError(
                    "resume STOP: repository dispatch gates failed: "
                    + "; ".join(check["reasons"])
                )

        issue = self.request("GET", f"/issues/{number}")
        labels = [item["name"] for item in issue.get("labels", [])]
        final_labels = next_labels(labels, status, self.config)
        safe_labels = [label for label in labels if label != routing_name(self.config)]

        # Routing stays disabled until every repository-native status update
        # succeeds. A partial transition therefore cannot dispatch more work.
        self.request("PATCH", f"/issues/{number}", {"labels": safe_labels})

        try:
            updated_body = set_workflow_status(
                issue["body"], "blocked" if status == "failed" else status
            )
            if status == "blocked" and block_kind == "decision":
                updated_body = set_human_gate(updated_body, "required")
            elif status == "scheduled" and clear_human_gate:
                updated_body = set_human_gate(updated_body, "clear")
            self.request(
                "PATCH",
                f"/issues/{number}",
                {"body": updated_body},
            )
            if status_authority(self.config) == "github-project":
                event = runtime_event_for(status, block_kind)
                if event is not None:
                    transition_event(self.repo, number, event, self.config)
            self.request("POST", f"/issues/{number}/comments", {"body": comment})
            if final_labels != safe_labels:
                self.request(
                    "PATCH",
                    f"/issues/{number}",
                    {"labels": final_labels},
                )
        except Exception as error:
            mismatch = decision_comment(
                "State transition incomplete",
                f"routing remains disabled because repository status update failed: {error}",
            )
            try:
                self.request("POST", f"/issues/{number}/comments", {"body": mismatch})
            except Exception:
                pass
            raise


def validate_transition_marker(marker):
    if not isinstance(marker, dict) or marker.get("schema") != TRANSITION_SCHEMA:
        raise ValueError("unsupported transition marker schema")
    for key, limit in (("run_id", 200), ("attempt", 50), ("reason", 2000)):
        value = marker.get(key)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ValueError(f"transition marker {key} is invalid")
    if marker.get("transition") not in ("blocked", "review", "failed"):
        raise ValueError("transition marker transition is unknown")
    if marker.get("block_kind", "external") not in ("decision", "external"):
        raise ValueError("transition marker block_kind is invalid")
    return marker


def marker_comment(marker):
    return decision_comment(
        "Task lifecycle transition",
        marker["reason"],
    ) + (
        f"- run_id: `{sanitize(marker['run_id'])}`\n"
        f"- attempt: `{sanitize(marker['attempt'])}`\n"
        f"- transition: `{marker['transition']}`\n"
    )


def fail_closed_marker(github, issue_number, reason):
    github.transition(
        issue_number,
        "blocked",
        decision_comment("State marker rejected", reason),
        block_kind="external",
    )
    return "blocked"


def receipt_path(marker, receipt_dir):
    name = marker.get("receipt") if isinstance(marker, dict) else None
    if not isinstance(name, str) or not re.fullmatch(r"[0-9a-f]{64}\.json", name):
        return None
    return receipt_dir / name


def transition_identity(repo, issue_number, marker):
    return "\0".join((
        repo,
        str(issue_number),
        marker["run_id"],
        marker["attempt"],
        marker["transition"],
    ))


def validated_receipt(tombstone, receipt_dir, repo, issue_number):
    receipt = receipt_path(tombstone, receipt_dir)
    if not isinstance(tombstone, dict) or tombstone.get("schema") != RECEIPT_SCHEMA or receipt is None:
        return None
    try:
        record = json.loads(receipt.read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            return None
        marker = validate_transition_marker(record["marker"])
    except (FileNotFoundError, OSError, KeyError, ValueError, json.JSONDecodeError):
        return None
    identity = transition_identity(repo, issue_number, marker)
    expected = hashlib.sha256(identity.encode()).hexdigest() + ".json"
    if record.get("issue") != issue_number or receipt.name != expected:
        return None
    return receipt


def clear_applied_marker(marker_path, receipt_dir, repo, issue_number):
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
        return False
    if validated_receipt(marker, receipt_dir, repo, issue_number) is None:
        return False
    marker_path.unlink()
    return True


def apply_transition_marker(github, issue_number, marker_path, receipt_dir):
    try:
        raw_marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return fail_closed_marker(github, issue_number, "required structured state marker is missing")
    except (OSError, ValueError, json.JSONDecodeError):
        return fail_closed_marker(github, issue_number, "structured state marker is invalid; transition was not inferred")

    if validated_receipt(raw_marker, receipt_dir, github.repo, issue_number) is not None:
        return "duplicate"
    try:
        marker = validate_transition_marker(raw_marker)
    except ValueError:
        return fail_closed_marker(github, issue_number, "structured state marker is invalid; transition was not inferred")

    identity = transition_identity(github.repo, issue_number, marker)
    receipt = receipt_dir / (hashlib.sha256(identity.encode()).hexdigest() + ".json")
    if receipt.exists():
        tombstone = {"schema": RECEIPT_SCHEMA, "receipt": receipt.name}
        if validated_receipt(tombstone, receipt_dir, github.repo, issue_number) is None:
            return fail_closed_marker(github, issue_number, "structured state receipt is invalid")
        marker_path.write_text(
            json.dumps(tombstone) + "\n",
            encoding="utf-8",
        )
        return "duplicate"

    github.transition(
        issue_number,
        marker["transition"],
        marker_comment(marker),
        block_kind=marker.get("block_kind", "external"),
    )
    receipt_dir.mkdir(parents=True, exist_ok=True)
    temporary = receipt.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"issue": issue_number, "marker": marker}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(receipt)
    marker_path.write_text(
        json.dumps({"schema": RECEIPT_SCHEMA, "receipt": receipt.name}) + "\n",
        encoding="utf-8",
    )
    return "applied"


def workspace_decision(status, local_sha, remote_sha):
    if status and local_sha != remote_sha:
        return "block"
    if status:
        return "continue"
    return "refresh"


def issue_from_workspace(workspace):
    match = re.fullmatch(r"GH-(\d+)", workspace.resolve().name)
    if not match:
        raise ValueError("workspace basename must be GH-<number>")
    return int(match.group(1))


def command(*args, cwd):
    return subprocess.run(
        args,
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def prepare_workspace(repo, workspace):
    issue_number = issue_from_workspace(workspace)
    clear_applied_marker(
        workspace / MARKER_FILENAME,
        default_receipt_dir(repo),
        repo,
        issue_number,
    )
    status = command("git", "status", "--porcelain", "--untracked-files=all", cwd=workspace)
    branch = command(
        "gh", "repo", "view", repo,
        "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name",
        cwd=workspace,
    )
    command("git", "fetch", "--prune", "origin", branch, cwd=workspace)
    local_sha = command("git", "rev-parse", "HEAD", cwd=workspace)
    remote_sha = command("git", "rev-parse", f"origin/{branch}", cwd=workspace)
    action = workspace_decision(status, local_sha, remote_sha)
    if action == "block":
        return {
            "schema": TRANSITION_SCHEMA,
            "issue": issue_number,
            "run_id": f"workspace-preflight-{local_sha[:12]}-{remote_sha[:12]}",
            "attempt": "before-run",
            "transition": "blocked",
            "block_kind": "external",
            "reason": sanitize(
                "dirty workspace base drift; Codex was not started. "
                f"local={local_sha} remote={remote_sha}. "
                "Preserve provenance and hashes in host-local recovery storage, then repair the workspace."
            ),
        }
    if action == "refresh":
        command("git", "reset", "--hard", f"origin/{branch}", cwd=workspace)
    return None


def default_receipt_dir(repo):
    state_home = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    return state_home / "excellent-nd" / "transition-receipts" / repo.replace("/", "_")


def worker_started_comment():
    return decision_comment(
        "Execution started",
        "Symphony emitted the deterministic worker-attempt start event",
    )


def apply_hook_transition(github, line, context):
    if "Workspace hook failed hook=before_run" not in line or TRANSITION_PREFIX not in line:
        return None
    try:
        marker = validate_transition_marker(decode_transition_event(line))
        if marker.get("issue") != context["issue_number"] or marker["transition"] != "blocked":
            raise ValueError("before-run marker identity or transition is invalid")
    except ValueError:
        github.transition(
            context["issue_number"],
            "blocked",
            decision_comment(
                "Workspace preparation marker rejected",
                "invalid structured before-run marker; transition was not inferred",
            ),
            block_kind="external",
        )
        return "blocked"
    github.transition(
        marker["issue"],
        "blocked",
        marker_comment(marker),
        block_kind=marker.get("block_kind", "external"),
    )
    return "blocked"


def interruption_workpad(category, line, context):
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    def shown(value):
        return value or "取得不能（runtime event に非搭載）"
    return f"""## Interruption Workpad

- workflow status: `blocked`
- interruption category: `{category}`
- error: `{sanitize(line)}`
- occurred_at: `{now}`
- reset_at: `{shown(context["reset_at"])}`
- retry_after: `{shown(context["retry_after"])}`
- session: `{shown(context["session_id"])}`
- attempt: `{shown(context["attempt"])}`
- last checkpoint (branch / commit / PR): 取得不能（runtime event に非搭載）。既存 Workpad / PR を確認する。
- remaining work: interruption 発生時点の Acceptance criteria 未完了項目を確認する。
- recommended resume condition: repository-native gatesを満たした後、Taskの `dispatch_scope` / `human_gate` を確認する。Plan継続が許可されhuman gateがclearなら後続Chat reconciliationで継続できる。human decisionが必要な場合だけ新しい人間指示を要求する。特別な承認フレーズは要求しない。

Error text is sanitized. Raw logs and credentials are not copied here.
"""


def symphony_command(args, logs_root=None):
    command = [args.symphony]
    if args.acknowledge_unguarded_preview:
        command.append(SYMPHONY_ACK_FLAG)
    if logs_root is not None:
        command.extend(["--logs-root", str(logs_root)])
    command.append(args.workflow)
    return command


def process_runtime_line(github, line, recorded):
    started_issue = worker_started_issue(line)
    start_key = (started_issue, "worker_start", line)
    if started_issue is not None and start_key not in recorded:
        github.transition(started_issue, "running", worker_started_comment())
        recorded.add(start_key)
    category = classify_interruption(line)
    context = extract_context(line)
    hook_key = (context["issue_number"], line)
    if (
        context["issue_number"]
        and hook_key not in recorded
        and apply_hook_transition(github, line, context)
    ):
        recorded.add(hook_key)
    key = (context["issue_number"], category)
    if category and context["issue_number"] and key not in recorded:
        github.transition(
            context["issue_number"],
            "blocked",
            interruption_workpad(category, line, context),
            block_kind="external",
        )
        recorded.add(key)


def run_observer(args):
    config = read_config(args.repository_config)
    github = GitHub(args.repo, config)
    logs_root = Path.cwd()
    follower = RotatingLogFollower(logs_root / "log" / "symphony.log")
    process = subprocess.Popen(
        symphony_command(args, logs_root=logs_root),
        stderr=subprocess.STDOUT,
    )
    recorded = RecentKeys()
    try:
        while process.poll() is None:
            for line in follower.poll():
                process_runtime_line(github, line, recorded)
            time.sleep(LOG_POLL_INTERVAL)
        while True:
            for line in follower.poll():
                process_runtime_line(github, line, recorded)
            if follower.last_bytes_read == 0:
                break
        follower.assert_available()
        return process.wait()
    except Exception:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        raise
    finally:
        follower.close()


def decision_comment(title, reason):
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return f"## {title}\n\n- decided_at: `{now}`\n- reason: {sanitize(reason)}\n"


def add_repository_config_argument(parser):
    parser.add_argument(
        "--repository-config",
        type=Path,
        default=Path(".excellent-nd/repository.json"),
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run")
    run.add_argument("--repo", required=True)
    run.add_argument("--workflow", required=True)
    run.add_argument("--symphony", required=True)
    run.add_argument(
        SYMPHONY_ACK_FLAG,
        dest="acknowledge_unguarded_preview",
        action="store_true",
        help="explicitly acknowledge Symphony preview execution without the usual guardrails",
    )
    add_repository_config_argument(run)

    resume = sub.add_parser("resume")
    resume.add_argument("--repo", required=True)
    resume.add_argument("--issue", type=int, required=True)
    resume.add_argument("--reason", required=True)
    resume.add_argument("--human-instruction", action="store_true")
    resume.add_argument(
        "--explicit-mention",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    resume.add_argument("--plan-continuation", action="store_true")
    resume.add_argument("--plan-ref")
    add_repository_config_argument(resume)

    state = sub.add_parser("state")
    state.add_argument("--repo", required=True)
    state.add_argument("--issue", type=int, required=True)
    state.add_argument("--status", choices=("blocked", "review", "failed"), required=True)
    state.add_argument("--block-kind", choices=("decision", "external"), default="external")
    state.add_argument("--reason", required=True)
    add_repository_config_argument(state)

    before_run = sub.add_parser("before-run")
    before_run.add_argument("--repo", required=True)
    before_run.add_argument("--workspace", type=Path, default=Path.cwd())

    marker = sub.add_parser("apply-marker")
    marker.add_argument("--repo", required=True)
    marker.add_argument("--workspace", type=Path, default=Path.cwd())
    marker.add_argument("--marker", type=Path, default=Path(MARKER_FILENAME))
    marker.add_argument("--receipt-dir", type=Path)
    add_repository_config_argument(marker)

    args = parser.parse_args(argv)
    if args.command == "run":
        return run_observer(args)
    if args.command == "before-run":
        try:
            event = prepare_workspace(args.repo, args.workspace)
        except Exception as error:
            event = {
                "schema": TRANSITION_SCHEMA,
                "issue": issue_from_workspace(args.workspace),
                "run_id": "workspace-preflight-failed",
                "attempt": "before-run",
                "transition": "blocked",
                "block_kind": "external",
                "reason": f"workspace preparation failed; Codex was not started: {sanitize(str(error))}",
            }
        if event is not None:
            print(encode_transition_event(event))
            return 75
        return 0

    if args.command == "resume":
        human_instruction = args.human_instruction or args.explicit_mention
        if human_instruction and args.plan_continuation:
            parser.error("resume authorization modes are mutually exclusive")
        if not human_instruction and not args.plan_continuation:
            parser.error("resume requires --human-instruction or --plan-continuation")
        if args.plan_continuation and not args.plan_ref:
            parser.error("--plan-continuation requires --plan-ref")

    config = read_config(args.repository_config)
    github = GitHub(args.repo, config)
    if args.command == "apply-marker":
        issue_number = issue_from_workspace(args.workspace)
        receipt_dir = args.receipt_dir or default_receipt_dir(args.repo)
        return 0 if apply_transition_marker(
            github,
            issue_number,
            args.workspace / args.marker,
            receipt_dir,
        ) in ("applied", "duplicate", "blocked") else 1
    if args.command == "resume":
        human_instruction = args.human_instruction or args.explicit_mention
        if args.plan_continuation:
            github.validate_plan_continuation(args.issue, args.plan_ref)
        github.transition(
            args.issue,
            "scheduled",
            decision_comment(
                "Resume decision" if human_instruction else "Plan continuation",
                args.reason,
            ),
            clear_human_gate=human_instruction,
        )
    else:
        github.transition(
            args.issue,
            args.status,
            decision_comment("State decision", args.reason),
            block_kind=args.block_kind,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
