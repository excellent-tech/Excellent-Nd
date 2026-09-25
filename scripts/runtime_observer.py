#!/usr/bin/env python3
"""Run Symphony and synchronize non-transient interruptions with a GitHub Issue."""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from repository_config import read_config, routing_name, status_name, status_names

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


def next_labels(labels, status, config):
    route = routing_name(config)
    configured_statuses = status_names(config)
    kept = [label for label in labels if label != route and label not in configured_statuses]
    if status == "scheduled":
        kept.append(route)
    kept.append(status_name(config, status))
    return kept


class GitHub:
    def __init__(self, repo, config, token=None):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("repo must be owner/name")
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

    def transition(self, number, status, comment):
        issue = self.request("GET", f"/issues/{number}")
        labels = [item["name"] for item in issue.get("labels", [])]
        self.request(
            "PATCH",
            f"/issues/{number}",
            {
                "body": set_workflow_status(issue["body"], "blocked" if status == "failed" else status),
                "labels": next_labels(labels, status, self.config),
            },
        )
        self.request("POST", f"/issues/{number}/comments", {"body": comment})


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
- recommended resume condition: 原因を解消し、現在の user message で明示的な `@excellent-nd` と人間による実行承認（Human GO）を確認する。

Error text is sanitized. Raw logs and credentials are not copied here.
"""


def run_observer(args):
    config = read_config(args.repository_config)
    github = GitHub(args.repo, config)
    process = subprocess.Popen(
        [args.symphony, args.workflow],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    recorded = set()
    assert process.stdout is not None
    for raw in process.stdout:
        sys.stdout.write(raw)
        line = raw.rstrip()
        category = classify_interruption(line)
        context = extract_context(line)
        key = (context["issue_number"], category)
        if category and context["issue_number"] and key not in recorded:
            github.transition(
                context["issue_number"], "blocked",
                interruption_workpad(category, line, context),
            )
            recorded.add(key)
    return process.wait()


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
    add_repository_config_argument(run)

    resume = sub.add_parser("resume")
    resume.add_argument("--repo", required=True)
    resume.add_argument("--issue", type=int, required=True)
    resume.add_argument("--reason", required=True)
    resume.add_argument("--explicit-mention", action="store_true")
    resume.add_argument("--human-go", action="store_true")
    add_repository_config_argument(resume)

    state = sub.add_parser("state")
    state.add_argument("--repo", required=True)
    state.add_argument("--issue", type=int, required=True)
    state.add_argument("--status", choices=("blocked", "review", "failed"), required=True)
    state.add_argument("--reason", required=True)
    add_repository_config_argument(state)

    args = parser.parse_args(argv)
    if args.command == "run":
        return run_observer(args)

    config = read_config(args.repository_config)
    github = GitHub(args.repo, config)
    if args.command == "resume":
        if not (args.explicit_mention and args.human_go):
            parser.error("resume requires --explicit-mention and --human-go")
        github.transition(args.issue, "scheduled", decision_comment("Resume decision", args.reason))
    else:
        github.transition(args.issue, args.status, decision_comment("State decision", args.reason))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
