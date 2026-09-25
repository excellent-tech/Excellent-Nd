#!/usr/bin/env python3
"""Repository-level Issue integration configuration for Excellent-Nd."""

from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

from execution_target import routing_label

SCHEMA = "excellent-nd/repository@v1"
MANAGEMENT = {"existing", "excellent-nd"}
STATUS_ROLES = ("scheduled", "running", "blocked", "review", "failed")
LABEL_NAME_MAX = 50
TARGET_PREFIX_MAX = 10
_TARGET_PREFIX_RE = re.compile(r"^[a-z0-9._:-]+$")

STANDARD_STYLES = {
    "routing": ("0E8A16", "Excellent-Nd routing / execution control"),
    "scheduled": ("C2E0C6", "Human GO complete; waiting to run"),
    "running": ("1D76DB", "Codex execution in progress"),
    "blocked": ("D93F0B", "Waiting for human, external condition, or quota"),
    "review": ("FBCA04", "Waiting for human review"),
    "failed": ("B60205", "Cannot continue automatically; inspect the cause"),
    "target": ("5319E7", "Excellent-Nd execution target"),
}

_DEFAULT_CONFIG = {
    "schema": SCHEMA,
    "issue_integration": {
        "reviewed": {
            "labels": True,
            "issue_templates": True,
            "automation": True,
        },
        "issue_templates": {
            "policy": "preserve",
        },
        "labels": {
            "routing": {
                "name": "symphony-ready",
                "management": "excellent-nd",
            },
            "status": {
                "scheduled": {"name": "nd-status:scheduled", "management": "excellent-nd"},
                "running": {"name": "nd-status:running", "management": "excellent-nd"},
                "blocked": {"name": "nd-status:blocked", "management": "excellent-nd"},
                "review": {"name": "nd-status:review", "management": "excellent-nd"},
                "failed": {"name": "nd-status:failed", "management": "excellent-nd"},
            },
            "target": {
                "prefix": "nd-target:",
                "management": "excellent-nd",
            },
        },
    },
}


def default_config() -> dict:
    return copy.deepcopy(_DEFAULT_CONFIG)


def config_path(repo_root: Path) -> Path:
    return repo_root / ".excellent-nd" / "repository.json"


def _validate_label_name(name: object, field: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{field} must be a non-empty string")
    if len(name) > LABEL_NAME_MAX:
        raise ValueError(f"{field} exceeds GitHub label limit ({LABEL_NAME_MAX})")
    return name


def _validate_management(value: object, field: str) -> str:
    if value not in MANAGEMENT:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(MANAGEMENT))}")
    return str(value)


def validate_config(config: dict) -> dict:
    if not isinstance(config, dict):
        raise ValueError("repository config must be an object")
    if config.get("schema") != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA}")
    integration = config.get("issue_integration")
    if not isinstance(integration, dict):
        raise ValueError("issue_integration is required")

    reviewed = integration.get("reviewed")
    if not isinstance(reviewed, dict):
        raise ValueError("issue_integration.reviewed is required")
    for item in ("labels", "issue_templates", "automation"):
        if reviewed.get(item) is not True:
            raise ValueError(
                f"issue_integration.reviewed.{item} must be true before execution-host setup"
            )

    template = integration.get("issue_templates")
    if not isinstance(template, dict) or template.get("policy") not in {
        "preserve",
        "customized",
        "not-used",
    }:
        raise ValueError(
            "issue_templates.policy must be preserve, customized, or not-used"
        )

    labels = integration.get("labels")
    if not isinstance(labels, dict):
        raise ValueError("issue_integration.labels is required")
    routing = labels.get("routing")
    if not isinstance(routing, dict):
        raise ValueError("routing label config is required")
    _validate_label_name(routing.get("name"), "labels.routing.name")
    _validate_management(routing.get("management"), "labels.routing.management")

    status = labels.get("status")
    if not isinstance(status, dict):
        raise ValueError("status label config is required")

    names = [routing["name"]]
    for role in STATUS_ROLES:
        entry = status.get(role)
        if not isinstance(entry, dict):
            raise ValueError(f"status label config missing: {role}")
        names.append(_validate_label_name(entry.get("name"), f"labels.status.{role}.name"))
        _validate_management(
            entry.get("management"), f"labels.status.{role}.management"
        )
    if len(names) != len(set(names)):
        raise ValueError("routing/status semantic roles must use distinct label names")

    target = labels.get("target")
    if not isinstance(target, dict):
        raise ValueError("target label config is required")
    prefix = target.get("prefix")
    if (
        not isinstance(prefix, str)
        or not prefix
        or len(prefix) > TARGET_PREFIX_MAX
        or not _TARGET_PREFIX_RE.fullmatch(prefix)
    ):
        raise ValueError(
            f"labels.target.prefix must be 1-{TARGET_PREFIX_MAX} lowercase-safe characters"
        )
    _validate_management(target.get("management"), "labels.target.management")
    return config


def read_config(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(
            f"repository integration config is missing: {path}; complete Chat-first repository integration before host setup"
        )
    return validate_config(json.loads(path.read_text(encoding="utf-8")))


def load_repository_config(repo_root: Path) -> dict:
    return read_config(config_path(repo_root))


def routing_name(config: dict) -> str:
    return config["issue_integration"]["labels"]["routing"]["name"]


def target_prefix(config: dict) -> str:
    return config["issue_integration"]["labels"]["target"]["prefix"]


def status_name(config: dict, status: str) -> str:
    if status not in STATUS_ROLES:
        raise ValueError(f"unsupported status: {status}")
    return config["issue_integration"]["labels"]["status"][status]["name"]


def status_names(config: dict) -> set[str]:
    return {status_name(config, role) for role in STATUS_ROLES}


def label_specs(config: dict, execution_target: str) -> list[dict]:
    validate_config(config)
    labels = config["issue_integration"]["labels"]
    specs = [{
        "role": "routing",
        "name": labels["routing"]["name"],
        "management": labels["routing"]["management"],
        "color": STANDARD_STYLES["routing"][0],
        "description": STANDARD_STYLES["routing"][1],
    }]
    for role in STATUS_ROLES:
        entry = labels["status"][role]
        specs.append({
            "role": role,
            "name": entry["name"],
            "management": entry["management"],
            "color": STANDARD_STYLES[role][0],
            "description": STANDARD_STYLES[role][1],
        })
    target = labels["target"]
    specs.append({
        "role": "target",
        "name": routing_label(execution_target, target["prefix"]),
        "management": target["management"],
        "color": STANDARD_STYLES["target"][0],
        "description": f"Excellent-Nd execution target: {execution_target}",
    })
    return specs


def plan_label_actions(
    config: dict, execution_target: str, existing_names: set[str]
) -> list[dict]:
    actions = []
    for spec in label_specs(config, execution_target):
        if spec["name"] in existing_names:
            actions.append({**spec, "action": "preserve"})
        elif spec["management"] == "existing":
            raise ValueError(
                f"required existing label is missing for role {spec['role']}: {spec['name']}"
            )
        else:
            actions.append({**spec, "action": "create"})
    return actions


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init-standard")
    init.add_argument("--repo-root", type=Path, default=Path("."))

    validate = sub.add_parser("validate")
    validate.add_argument("--repo-root", type=Path, default=Path("."))

    args = parser.parse_args(argv)
    root = args.repo_root.resolve()
    path = config_path(root)

    if args.command == "init-standard":
        if path.exists():
            raise RuntimeError(f"refusing to overwrite existing repository config: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(default_config(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(path)
        return 0

    read_config(path)
    print("repository integration: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
