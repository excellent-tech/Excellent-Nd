#!/usr/bin/env python3
"""Compatibility wrapper for the generic repository adapter."""

from repository_adapter import *  # noqa: F401,F403
from repository_adapter import main

if __name__ == "__main__":
    raise SystemExit(main())
