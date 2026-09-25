#!/usr/bin/env python3
"""Fail-closed repository mapping and gate adapter for Excellent-Nd."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Callable

from repository_config import (
    RUNTIME_EVENTS,
    dispatch_gates,
    github_project,
    project_event_value,
    read_config,
    status_authority,
    uses_github_project,
)

ISSUE_CONTEXT_QUERY = r"""
query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    issue(number:$number) {
      number
      state
      labels(first:100) {
        nodes { name }
        pageInfo { hasNextPage }
      }
      projectItems(first:20) {
        nodes {
          id
          project { id title number }
          fieldValues(first:100) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                optionId
                field {
                  ... on ProjectV2SingleSelectField {
                    id
                    name
                    options { id name }
                  }
                }
              }
            }
            pageInfo { hasNextPage }
          }
        }
        pageInfo { hasNextPage }
      }
    }
  }
}
"""

UPDATE_STATUS_MUTATION = r"""
mutation($project:ID!, $item:ID!, $field:ID!, $option:String!) {
  updateProjectV2ItemFieldValue(input:{
    projectId:$project,
    itemId:$item,
    fieldId:$field,
    value:{singleSelectOptionId:$option}
  }) {
    projectV2Item { id }
  }
}
"""


def split_repo(repo: str) -> tuple[str, str]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("repo must be owner/name")
    return tuple(repo.split("/", 1))


def gh_graphql(args: list[str]) -> dict:
    completed = subprocess.run(
        ["gh", "api", "graphql", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(completed.stdout)


def fetch_snapshot(
    repo: str,
    issue_number: int,
    runner: Callable[[list[str]], dict] = gh_graphql,
) -> dict:
    owner, name = split_repo(repo)
    return runner([
        "-f", f"query={ISSUE_CONTEXT_QUERY}",
        "-F", f"owner={owner}",
        "-F", f"repo={name}",
        "-F", f"number={issue_number}",
    ])


def resolve_context(snapshot: dict, config: dict) -> dict:
    repository = (snapshot.get("data") or {}).get("repository")
    issue = repository.get("issue") if isinstance(repository, dict) else None
    if not isinstance(issue, dict):
        raise ValueError("repository preflight STOP: issue data unavailable")

    labels_block = issue.get("labels") or {}
    labels = {
        node.get("name")
        for node in (labels_block.get("nodes") or [])
        if isinstance(node, dict) and isinstance(node.get("name"), str)
    }
    labels_complete = not bool((labels_block.get("pageInfo") or {}).get("hasNextPage"))

    context = {
        "issue_state": str(issue.get("state") or "").lower() or None,
        "labels": labels,
        "labels_complete": labels_complete,
        "project_id": None,
        "project_item_id": None,
        "project_title": None,
        "project_fields": {},
        "project_fields_complete": True,
    }

    if not uses_github_project(config):
        return context

    project_cfg = github_project(config)
    project_items_block = issue.get("projectItems") or {}
    if (project_items_block.get("pageInfo") or {}).get("hasNextPage"):
        raise ValueError(
            "repository preflight STOP: project item list is paginated; exact project identity is not provable"
        )

    items = project_items_block.get("nodes") or []
    matches = [
        item for item in items
        if isinstance(item, dict)
        and isinstance(item.get("project"), dict)
        and item["project"].get("title") == project_cfg["title"]
    ]
    if len(matches) != 1:
        raise ValueError(
            "repository preflight STOP: expected exactly one matching project item, "
            f"found {len(matches)} for {project_cfg['title']!r}"
        )

    item = matches[0]
    fields_block = item.get("fieldValues") or {}
    if (fields_block.get("pageInfo") or {}).get("hasNextPage"):
        raise ValueError(
            "repository preflight STOP: project field values are paginated; field completeness is not provable"
        )

    fields = {}
    for node in (fields_block.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        field = node.get("field")
        if not isinstance(field, dict) or not isinstance(field.get("name"), str):
            continue
        fields[field["name"]] = {
            "value": node.get("name"),
            "option_id": node.get("optionId"),
            "field_id": field.get("id"),
            "options": {
                option.get("name"): option.get("id")
                for option in (field.get("options") or [])
                if isinstance(option, dict)
                and isinstance(option.get("name"), str)
                and isinstance(option.get("id"), str)
            },
        }

    context.update({
        "project_id": (item.get("project") or {}).get("id"),
        "project_item_id": item.get("id"),
        "project_title": (item.get("project") or {}).get("title"),
        "project_fields": fields,
    })
    return context


def _gate_failure(gate: dict, actual: object) -> str:
    return (
        f"gate {gate['id']!r} failed: source={gate['source']} "
        f"operator={gate['operator']} actual={actual!r}"
    )


def evaluate_gates(context: dict, config: dict) -> dict:
    reasons = []
    observed = {}

    for gate in dispatch_gates(config):
        gate_id = gate["id"]
        source = gate["source"]
        operator = gate["operator"]

        if source == "github-project-field":
            field = gate["field"]
            field_data = context["project_fields"].get(field)
            actual = field_data.get("value") if isinstance(field_data, dict) else None
            observed[gate_id] = actual
            if actual is None:
                reasons.append(f"gate {gate_id!r} STOP: project field {field!r} is unavailable")
                continue
            if operator == "equals":
                passed = actual == gate["value"]
            elif operator == "not-equals":
                passed = actual != gate["value"]
            elif operator == "in":
                passed = actual in gate["values"]
            else:
                passed = actual not in gate["values"]
            if not passed:
                reasons.append(_gate_failure(gate, actual))

        elif source == "label":
            if not context["labels_complete"]:
                reasons.append(f"gate {gate_id!r} STOP: label list is paginated/incomplete")
                continue
            configured = set(gate["values"])
            present = sorted(configured & set(context["labels"]))
            observed[gate_id] = present
            passed = bool(present) if operator == "present" else not present
            if not passed:
                reasons.append(_gate_failure(gate, present))

        else:
            actual = context["issue_state"]
            observed[gate_id] = actual
            if actual is None:
                reasons.append(f"gate {gate_id!r} STOP: issue state is unavailable")
                continue
            passed = actual == gate["value"].lower() if operator == "equals" else actual in {
                value.lower() for value in gate["values"]
            }
            if not passed:
                reasons.append(_gate_failure(gate, actual))

    return {
        "result": "PASS" if not reasons else "STOP",
        "reasons": reasons,
        "observed": observed,
        "project": context["project_title"],
    }


def preflight(
    repo: str,
    issue_number: int,
    config: dict,
    runner: Callable[[list[str]], dict] = gh_graphql,
) -> dict:
    context = resolve_context(fetch_snapshot(repo, issue_number, runner), config)
    return evaluate_gates(context, config)


def transition_event(
    repo: str,
    issue_number: int,
    event: str,
    config: dict,
    runner: Callable[[list[str]], dict] = gh_graphql,
) -> dict:
    if status_authority(config) != "github-project":
        raise ValueError("repository status authority is not github-project")
    if event not in RUNTIME_EVENTS:
        raise ValueError(f"unsupported runtime event: {event}")

    status_cfg = config["issue_integration"]["status_integration"]
    mutable = set(status_cfg.get("mutable_events", []))
    if event not in mutable:
        raise ValueError(
            f"runtime event transition is not enabled for this repository: {event}"
        )

    context = resolve_context(fetch_snapshot(repo, issue_number, runner), config)
    field_name = status_cfg["field"]
    field = context["project_fields"].get(field_name)
    if not isinstance(field, dict) or not field.get("field_id"):
        raise ValueError(
            f"repository transition STOP: status field {field_name!r} unavailable"
        )

    desired = project_event_value(config, event)
    option_id = (field.get("options") or {}).get(desired)
    if not option_id:
        raise ValueError(
            f"repository transition STOP: option {desired!r} unavailable in {field_name!r}"
        )
    if not context.get("project_id") or not context.get("project_item_id"):
        raise ValueError("repository transition STOP: project/item identity unavailable")

    runner([
        "-f", f"query={UPDATE_STATUS_MUTATION}",
        "-F", f"project={context['project_id']}",
        "-F", f"item={context['project_item_id']}",
        "-F", f"field={field['field_id']}",
        "-F", f"option={option_id}",
    ])
    return {
        "result": "UPDATED",
        "event": event,
        "value": desired,
        "project": context["project_title"],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository-config",
        type=Path,
        default=Path(".excellent-nd/repository.json"),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("preflight")
    check.add_argument("--repo", required=True)
    check.add_argument("--issue", type=int, required=True)

    transition = sub.add_parser("transition")
    transition.add_argument("--repo", required=True)
    transition.add_argument("--issue", type=int, required=True)
    transition.add_argument("--event", choices=RUNTIME_EVENTS, required=True)

    args = parser.parse_args(argv)
    config = read_config(args.repository_config)
    if args.command == "preflight":
        result = preflight(args.repo, args.issue, config)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["result"] == "PASS" else 2

    result = transition_event(args.repo, args.issue, args.event, config)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
