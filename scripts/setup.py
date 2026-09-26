#!/usr/bin/env python3
"""Install the validated Symphony dependency after repository integration is approved."""

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

from execution_target import default_execution_target, normalize_execution_target, render_workflow, routing_label
from repository_config import (
    config_path,
    load_repository_config,
    plan_label_actions,
    routing_name,
    target_prefix,
    status_authority,
)
from target_inventory import write_target_record

SYMPHONY_ACK_FLAG = "--i-understand-that-this-will-be-running-without-the-usual-guardrails"


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


def command(*args):
    return subprocess.run(
        args,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    ).stdout.strip()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument("--execution-target", help="stable execution target ID; defaults to local hostname")
    parser.add_argument("--repo-path", type=Path, default=Path("."), help="local target repository root")
    parser.add_argument("--publish-hostname", action="store_true")
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--skill-confirmed", action="store_true")
    parser.add_argument("--start", action="store_true")
    parser.add_argument(
        SYMPHONY_ACK_FLAG,
        dest="acknowledge_unguarded_preview",
        action="store_true",
        help="explicitly acknowledge Symphony preview execution without the usual guardrails",
    )
    parser.add_argument("--manifest", type=Path, default=Path("config/runtime-lock.json"))
    parser.add_argument("--template", type=Path, default=Path("config/WORKFLOW.md.tpl"))
    args = parser.parse_args(argv)

    if not args.skill_confirmed:
        parser.error("confirm the ChatGPT Skill is enabled with --skill-confirmed")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
        parser.error("--repo must be owner/name")
    for executable in ("git", "gh", "codex"):
        if not shutil.which(executable):
            parser.error(f"missing prerequisite: {executable}")
    subprocess.run(["gh", "auth", "status"], check=True)

    repo_path = args.repo_path.resolve()
    try:
        repo_root = Path(command("git", "-C", str(repo_path), "rev-parse", "--show-toplevel"))
    except subprocess.CalledProcessError as error:
        parser.error(f"--repo-path must point inside a Git repository: {error}")

    try:
        repository_config = load_repository_config(repo_root)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))

    local_hostname = platform.node() or "unknown-host"
    try:
        execution_target = normalize_execution_target(args.execution_target or default_execution_target())
    except ValueError as error:
        parser.error(str(error))

    route_label = routing_name(repository_config)
    target_label = routing_label(execution_target, target_prefix(repository_config))

    existing_labels = set(
        command(
            "gh", "label", "list", "--repo", args.repo, "--limit", "1000",
            "--json", "name", "--jq", ".[].name"
        ).splitlines()
    )
    try:
        actions = plan_label_actions(repository_config, execution_target, existing_labels)
    except ValueError as error:
        parser.error(str(error))

    for action in actions:
        if action["action"] != "create":
            continue
        subprocess.run(
            [
                "gh", "label", "create", action["name"], "--repo", args.repo,
                "--color", action["color"], "--description", action["description"]
            ],
            check=True,
        )

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
        render_workflow(
            args.template.read_text(),
            args.repo,
            execution_target,
            routing_label_name=route_label,
            target_prefix=target_prefix(repository_config),
        ),
        encoding="utf-8",
    )
    host_config = {
        "schema": "excellent-nd/host@v1",
        "repository": args.repo,
        "execution_target": execution_target,
        "hostname": local_hostname,
        "routing_label": route_label,
        "target_label": target_label,
        "repository_config": str(config_path(repo_root).relative_to(repo_root)),
        "status_authority": status_authority(repository_config),
    }
    (args.prefix / "host.json").write_text(
        json.dumps(host_config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    smoke = Path(__file__).with_name("smoke.py")
    subprocess.run(
        [
            sys.executable, str(smoke),
            "--manifest", str(args.manifest),
            "--runtime", str(runtime),
            "--workflow", str(workflow),
            "--repo", args.repo,
            "--execution-target", execution_target,
            "--repository-config", str(config_path(repo_root)),
        ],
        check=True,
    )

    published_hostname = local_hostname if args.execution_target is None or args.publish_hostname else None
    inventory_path = write_target_record(
        repo_root,
        execution_target=execution_target,
        hostname=published_hostname,
        enabled=True,
        max_concurrent_agents=1,
    )

    observer = Path(__file__).with_name("runtime_observer.py")
    observer_command = [
        sys.executable, str(observer), "run",
        "--repo", args.repo,
        "--workflow", str(workflow),
        "--symphony", str(runtime),
    ]
    if args.acknowledge_unguarded_preview:
        observer_command.append(SYMPHONY_ACK_FLAG)
    observer_command.extend([
        "--repository-config", str(config_path(repo_root)),
    ])
    print("execution target:", execution_target)
    print("routing label:", route_label)
    print("target label:", target_label)
    print("repository config:", config_path(repo_root))
    print("target inventory:", inventory_path)
    print("runtime command:", " ".join(observer_command))
    if args.start:
        os.execv(sys.executable, observer_command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
