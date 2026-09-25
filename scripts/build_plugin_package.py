#!/usr/bin/env python3
"""Build the portable Excellent-Nd skill-only plugin ZIP deterministically."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "plugin.json",
    "skills/excellent-nd/SKILL.md",
    "skills/excellent-nd/agents/openai.yaml",
    "skills/excellent-nd/references/task-schema.md",
    "skills/excellent-nd/references/version-policy.md",
    "skills/excellent-nd/references/workflow.md",
    "skills/excellent-nd/references/repository-onboarding.md",
    "scripts/setup.py",
    "scripts/execution_target.py",
    "scripts/repository_config.py",
    "scripts/target_inventory.py",
    "scripts/smoke.py",
    "scripts/runtime_observer.py",
    "config/WORKFLOW.md.tpl",
    "config/repository-config.default.json",
    "config/runtime-lock.json",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
)
PACKAGE_ROOTS = (
    Path("plugin.json"),
    Path("skills/excellent-nd"),
    Path("scripts/setup.py"),
    Path("scripts/execution_target.py"),
    Path("scripts/repository_config.py"),
    Path("scripts/target_inventory.py"),
    Path("scripts/smoke.py"),
    Path("scripts/runtime_observer.py"),
    Path("config/WORKFLOW.md.tpl"),
    Path("config/repository-config.default.json"),
    Path("config/runtime-lock.json"),
    Path("LICENSE"),
    Path("THIRD_PARTY_NOTICES.md"),
)
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def validate_source(root: Path) -> dict:
    missing = [path for path in REQUIRED_FILES if not (root / path).is_file()]
    if missing:
        raise RuntimeError("missing required plugin files: " + ", ".join(missing))

    manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise RuntimeError("plugin.json must declare Agent Plugins schema 1.0.0")
    if manifest.get("name") != "excellent-nd":
        raise RuntimeError("plugin.json name must be excellent-nd")
    if not manifest.get("version"):
        raise RuntimeError("plugin.json version is required")
    if not manifest.get("description"):
        raise RuntimeError("plugin.json description is required")

    forbidden = ("mcp.json", ".mcp.json", ".app.json")
    present = [path for path in forbidden if (root / path).exists()]
    if present:
        raise RuntimeError(
            "skill-only package must not contain MCP/app configuration: " + ", ".join(present)
        )
    return manifest


def iter_package_files(root: Path):
    seen = set()
    for rel in PACKAGE_ROOTS:
        path = root / rel
        candidates = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        for candidate in candidates:
            if candidate.name == "__pycache__" or candidate.suffix == ".pyc":
                continue
            arcname = candidate.relative_to(root).as_posix()
            if arcname not in seen:
                seen.add(arcname)
                yield candidate, arcname


def build_package(root: Path, output: Path) -> str:
    validate_source(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, arcname in iter_package_files(root):
            info = zipfile.ZipInfo(arcname, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())

    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return digest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "excellent-nd-plugin.zip")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest = validate_source(ROOT)
    if args.check_only:
        print(f"PASS: excellent-nd plugin {manifest['version']} source is packageable")
        return 0

    digest = build_package(ROOT, args.output)
    print(f"PASS: wrote {args.output}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
