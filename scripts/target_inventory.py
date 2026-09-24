#!/usr/bin/env python3
"""Repository-local execution target inventory.

Only non-secret routing/capacity metadata is accepted. Credentials and arbitrary
extension fields are intentionally unsupported in v1.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from execution_target import normalize_execution_target, routing_label

SCHEMA = "excellent-nd/target@v1"
ALLOWED_FIELDS = {
    "schema",
    "id",
    "hostname",
    "enabled",
    "routing_label",
    "max_concurrent_agents",
    "last_verified_at",
}


def inventory_dir(repo_root: Path) -> Path:
    return repo_root / ".excellent-nd" / "targets"


def target_path(repo_root: Path, execution_target: str) -> Path:
    target = normalize_execution_target(execution_target)
    return inventory_dir(repo_root) / f"{target}.json"


def validate_record(record: dict) -> dict:
    unknown = set(record) - ALLOWED_FIELDS
    if unknown:
        raise ValueError("unsupported target inventory fields: " + ", ".join(sorted(unknown)))
    if record.get("schema") != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA}")
    target = normalize_execution_target(record.get("id", ""))
    if record.get("routing_label") != routing_label(target):
        raise ValueError("routing_label must match id")
    hostname = record.get("hostname")
    if hostname is not None and (not isinstance(hostname, str) or not hostname.strip()):
        raise ValueError("hostname must be a non-empty string or null")
    if not isinstance(record.get("enabled"), bool):
        raise ValueError("enabled must be boolean")
    concurrency = record.get("max_concurrent_agents")
    if not isinstance(concurrency, int) or isinstance(concurrency, bool) or concurrency < 1:
        raise ValueError("max_concurrent_agents must be a positive integer")
    stamp = record.get("last_verified_at")
    if not isinstance(stamp, str) or not stamp.endswith("Z"):
        raise ValueError("last_verified_at must be an ISO-8601 UTC string")
    return record


def write_target_record(
    repo_root: Path,
    *,
    execution_target: str,
    hostname: str | None,
    enabled: bool,
    max_concurrent_agents: int,
    verified_at: str | None = None,
) -> Path:
    target = normalize_execution_target(execution_target)
    stamp = verified_at or (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    record = {
        "schema": SCHEMA,
        "id": target,
        "hostname": hostname,
        "enabled": enabled,
        "routing_label": routing_label(target),
        "max_concurrent_agents": max_concurrent_agents,
        "last_verified_at": stamp,
    }
    validate_record(record)
    path = target_path(repo_root, target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_targets(repo_root: Path) -> list[dict]:
    directory = inventory_dir(repo_root)
    if not directory.exists():
        return []
    records = []
    for path in sorted(directory.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        validate_record(record)
        records.append(record)
    return records


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("list")
    show.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    records = load_targets(args.repo_root.resolve())
    print(json.dumps({
        "registered": len(records),
        "enabled": sum(1 for item in records if item["enabled"]),
        "targets": records,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
