#!/usr/bin/env python3
"""Execution-target identity and routing helpers."""

from __future__ import annotations

import re
import socket

TARGET_LABEL_PREFIX = "nd-target:"
MAX_TARGET_ID_LENGTH = 40
_TARGET_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{0,38}[a-z0-9])?$")


def normalize_execution_target(value: str) -> str:
    target = value.strip().lower().rstrip(".")
    if not target:
        raise ValueError("execution_target must not be empty")
    if len(target) > MAX_TARGET_ID_LENGTH or not _TARGET_RE.fullmatch(target):
        raise ValueError(
            "execution_target must be 1-40 characters using lowercase letters, digits, dots, or hyphens; "
            "it must start and end with a letter or digit"
        )
    return target


def default_execution_target() -> str:
    return normalize_execution_target(socket.gethostname())


def routing_label(value: str) -> str:
    return TARGET_LABEL_PREFIX + normalize_execution_target(value)


def render_workflow(template: str, repository: str, execution_target: str) -> str:
    return (
        template.replace("__REPOSITORY__", repository)
        .replace("__EXECUTION_TARGET_LABEL__", routing_label(execution_target))
    )
