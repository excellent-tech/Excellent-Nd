#!/usr/bin/env python3
"""Deterministic preflight checks for the validated Excellent-Nd runtime."""

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path


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


def require(condition, message):\n    if not condition:\n        raise RuntimeError(message)\n\n\ndef main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("config/runtime-lock.json"))
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--workflow", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text())
    asset = manifest["symphony"]["assets"][target()]
    require(digest(args.runtime) == asset["sha256"], "Symphony checksum mismatch")
    codex = command("codex", "--version")
    assert re.search(rf"\b{re.escape(manifest['codex']['version'])}\b", codex), f"unexpected Codex version: {codex}"
    command("gh", "auth", "status")
    workflow = args.workflow.read_text()
    require("__REPOSITORY__" not in workflow, "WORKFLOW placeholder was not rendered")
    require(args.repo in workflow, "WORKFLOW repository mismatch")
    require("{{ issue.description }}" in workflow, "WORKFLOW omits issue.description")
    require("symphony-ready" in workflow, "WORKFLOW omits routing label")
    require("approval_policy: never" in workflow, "WORKFLOW approval policy mismatch")
    require(os.access(args.runtime, os.X_OK), "Symphony binary is not executable")
    print("readiness: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
