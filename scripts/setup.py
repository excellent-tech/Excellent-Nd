#!/usr/bin/env python3
"""Install the validated Symphony dependency and render an Excellent-Nd profile."""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from execution_target import (
    default_execution_target,
    normalize_execution_target,
    render_workflow,
    routing_label,
)


LABELS = (
    ("symphony-ready", "0E8A16", "Routing / execution control"),
    ("nd-status:scheduled", "C2E0C6", "Human GO complete; waiting to run"),
    ("nd-status:running", "1D76DB", "Codex execution in progress"),
    ("nd-status:blocked", "D93F0B", "Waiting for human, external condition, or quota"),
    ("nd-status:review", "FBCA04", "Waiting for human review"),
    ("nd-status:failed", "B60205", "Cannot continue automatically; inspect the cause"),
)


def target():
    system = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    machine = {"x86_64": "x86_64", "AMD64": "x86_64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine())
    if not system or not machine:
        raise RuntimeError(f"unsupported platform: {platform.system()} {platform.machine()}")
    return f"{system}-{machine}"


def sha256(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def repo_visibility(repo):
    return subprocess.run(
        ["gh", "repo", "view", repo, "--json", "visibility", "--jq", ".visibility"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip().lower()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument(
        "--execution-target",
        help="stable execution target ID; defaults to local hostname for non-public repositories",
    )
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--skill-confirmed", action="store_true")
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--manifest", type=Path, default=Path("config/runtime-lock.json"))
    parser.add_argument("--template", type=Path, default=Path("config/WORKFLOW.md.tpl"))
    args = parser.parse_args(argv)

    if not args.skill_confirmed:
        parser.error("confirm the ChatGPT Skill is enabled with --skill-confirmed")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
        parser.error("--repo must be owner/name")
    for command in ("git", "gh", "codex"):
        if not shutil.which(command):
            parser.error(f"missing prerequisite: {command}")
    subprocess.run(["gh", "auth", "status"], check=True)

    visibility = repo_visibility(args.repo)
    if args.execution_target is None and visibility == "public":
        parser.error(
            "public repository requires --execution-target with a non-sensitive alias; "
            "refusing to publish the local hostname by default"
        )
    try:
        execution_target = normalize_execution_target(
            args.execution_target or default_execution_target()
        )
    except ValueError as error:
        parser.error(str(error))
    target_label = routing_label(execution_target)

    manifest = json.loads(args.manifest.read_text())
    asset = manifest["symphony"]["assets"].get(target())
    if not asset:
        parser.error(f"no validated Symphony asset for {target()}")
    args.prefix.mkdir(parents=True, exist_ok=True)
    runtime = args.prefix / "symphony"
    url = f"https://github.com/{manifest['symphony']['repository']}/releases/download/{manifest['symphony']['tag']}/{asset['name']}"
    if not runtime.exists() or sha256(runtime) != asset["sha256"]:
        temporary = runtime.with_suffix(".download")
        urllib.request.urlretrieve(url, temporary)
        if sha256(temporary) != asset["sha256"]:
            temporary.unlink(missing_ok=True)
            raise RuntimeError("downloaded Symphony checksum mismatch")
        temporary.replace(runtime)
    runtime.chmod(0o755)

    workflow = args.prefix / "WORKFLOW.md"
    workflow.write_text(
        render_workflow(args.template.read_text(), args.repo, execution_target),
        encoding="utf-8",
    )
    host_config = {
        "schema": "excellent-nd/host@v1",
        "repository": args.repo,
        "execution_target": execution_target,
        "routing_label": target_label,
    }
    (args.prefix / "host.json").write_text(
        json.dumps(host_config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    labels = LABELS + ((target_label, "5319E7", f"Execution target: {execution_target}"),)
    for name, color, description in labels:
        subprocess.run(
            ["gh", "label", "create", name, "--repo", args.repo, "--color", color, "--description", description, "--force"],
            check=True,
        )

    smoke = Path(__file__).with_name("smoke.py")
    subprocess.run(
        [
            sys.executable,
            str(smoke),
            "--manifest",
            str(args.manifest),
            "--runtime",
            str(runtime),
            "--workflow",
            str(workflow),
            "--repo",
            args.repo,
            "--execution-target",
            execution_target,
        ],
        check=True,
    )
    observer = Path(__file__).with_name("runtime_observer.py")
    command = [sys.executable, str(observer), "run", "--repo", args.repo, "--workflow", str(workflow), "--symphony", str(runtime)]
    print("execution target:", execution_target)
    print("routing label:", target_label)
    print("runtime command:", " ".join(command))
    if args.start:
        os.execv(sys.executable, command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
