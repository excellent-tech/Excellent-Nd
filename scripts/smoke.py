#!/usr/bin/env python3
"""Deterministic preflight checks for the validated Excellent-Nd runtime."""

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
from pathlib import Path

from execution_target import normalize_execution_target, routing_label
from repository_config import read_config, routing_name, target_prefix


def target():
    system = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    machine = {"x86_64": "x86_64", "AMD64": "x86_64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine())
    if not system or not machine:
        raise RuntimeError(f"unsupported platform: {platform.system()} {platform.machine()}")
    return f"{system}-{machine}"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def command(*args):
    return subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.strip()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("config/runtime-lock.json"))
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--execution-target", required=True)
    parser.add_argument("--repository-config", type=Path, required=True)
    args = parser.parse_args(argv)

    config = read_config(args.repository_config)
    execution_target = normalize_execution_target(args.execution_target)
    route_label = routing_name(config)
    target_label = routing_label(execution_target, target_prefix(config))
    manifest = json.loads(args.manifest.read_text())
    asset = manifest["symphony"]["assets"][target()]
    require(digest(args.runtime) == asset["sha256"], "Symphony checksum mismatch")
    codex = command("codex", "--version")
    require(re.search(rf"\b{re.escape(manifest['codex']['version'])}\b", codex), f"unexpected Codex version: {codex}")
    command("gh", "auth", "status")
    workflow = args.workflow.read_text()
    require("__REPOSITORY__" not in workflow, "WORKFLOW repository placeholder was not rendered")
    require("__ROUTING_LABEL__" not in workflow, "WORKFLOW routing placeholder was not rendered")
    require("__EXECUTION_TARGET_LABEL__" not in workflow, "WORKFLOW target placeholder was not rendered")
    require(args.repo in workflow, "WORKFLOW repository mismatch")
    require("{{ issue.description }}" in workflow, "WORKFLOW omits issue.description")
    require(route_label in workflow, "WORKFLOW omits configured routing label")
    require(target_label in workflow, "WORKFLOW omits configured target label")
    require("approval_policy: never" in workflow, "WORKFLOW approval policy mismatch")
    require("thread_sandbox: workspace-write" in workflow, "WORKFLOW sandbox policy mismatch")
    require("before_run:" in workflow, "WORKFLOW omits host-side before_run preparation")
    require("git fetch --prune origin" in workflow, "WORKFLOW omits host-side default-branch refresh")
    require("github_api" in workflow, "WORKFLOW omits host-side GitHub publication path")
    require("Git publication policy for `workspace-write`" in workflow, "WORKFLOW omits workspace-write Git publication policy")
    require("thread_sandbox: danger-full-access" not in workflow, "WORKFLOW must not enable danger-full-access")
    require(os.access(args.runtime, os.X_OK), "Symphony binary is not executable")
    print("readiness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
