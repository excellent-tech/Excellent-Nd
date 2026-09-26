#!/usr/bin/env python3
"""Start one repository observer from its host-local service mapping."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from systemd_service import mapping_path, validate_instance


ACK_FLAG = "--i-understand-that-this-will-be-running-without-the-usual-guardrails"
REPOSITORY_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
MAPPING_KEYS = {
    "schema", "repository", "repository_root", "workflow", "symphony", "host_config",
    "repository_config", "observer", "python", "path", "acknowledge_unguarded_preview",
}


def observer_command(mapping):
    command = [
        mapping["python"], mapping["observer"], "run",
        "--repo", mapping["repository"],
        "--workflow", mapping["workflow"],
        "--symphony", mapping["symphony"],
    ]
    if mapping["acknowledge_unguarded_preview"]:
        command.append(ACK_FLAG)
    command.extend(["--repository-config", mapping["repository_config"]])
    return command


def validate_mapping(mapping):
    path_keys = MAPPING_KEYS - {"schema", "repository", "path", "acknowledge_unguarded_preview"}
    if (
        not isinstance(mapping, dict)
        or set(mapping) != MAPPING_KEYS
        or mapping.get("schema") != "excellent-nd/service-instance@v1"
        or not isinstance(mapping.get("repository"), str)
        or not REPOSITORY_RE.fullmatch(mapping["repository"])
        or not isinstance(mapping.get("path"), str)
        or not mapping["path"]
        or type(mapping.get("acknowledge_unguarded_preview")) is not bool
        or any(not isinstance(mapping.get(key), str) or not Path(mapping[key]).is_absolute() for key in path_keys)
    ):
        raise RuntimeError("invalid service instance mapping")
    return mapping


def load_mapping(instance):
    mapping = validate_mapping(
        json.loads(mapping_path(validate_instance(instance)).read_text(encoding="utf-8"))
    )
    root = Path(mapping["repository_root"]).resolve()
    prefix = root / ".excellent-nd"
    expected = {
        "workflow": prefix / "WORKFLOW.md",
        "symphony": prefix / "symphony",
        "host_config": prefix / "host.json",
        "repository_config": prefix / "repository.json",
    }
    if not (root / ".git").exists():
        raise RuntimeError("mapped repository root is not a Git worktree")
    for key, path in expected.items():
        if Path(mapping[key]).resolve() != path.resolve() or not path.exists():
            raise RuntimeError(f"invalid or missing mapped {key}")
    for key in ("observer", "python"):
        if not Path(mapping[key]).is_file():
            raise RuntimeError(f"missing mapped {key}")
    host = json.loads(expected["host_config"].read_text(encoding="utf-8"))
    if host.get("repository") != mapping["repository"]:
        raise RuntimeError("host identity does not match service mapping")
    return mapping


def credential_environment(path):
    token = subprocess.run(
        ["gh", "auth", "token"], check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, "PATH": path},
    ).stdout.strip()
    if not token:
        raise RuntimeError("gh auth token returned an empty credential")
    return {**os.environ, "PATH": path, "GITHUB_TOKEN": token}


def run(instance):
    mapping = load_mapping(instance)
    environment = credential_environment(mapping["path"])
    command = observer_command(mapping)
    os.chdir(mapping["repository_root"])
    os.execve(command[0], command, environment)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) != 1:
        raise SystemExit("usage: service_runner.py INSTANCE")
    run(argv[0])


if __name__ == "__main__":
    main()
