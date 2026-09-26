"""Install and validate repository-scoped systemd user services."""

import json
import fcntl
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path


UNIT_NAME = "excellent-nd@.service"
INSTANCE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}")


def validate_instance(value):
    if not INSTANCE_RE.fullmatch(value):
        raise ValueError("service instance must match [A-Za-z0-9][A-Za-z0-9_.-]{0,79}")
    return value


def config_home():
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))


def mapping_path(instance):
    return config_home() / "excellent-nd" / "instances" / f"{validate_instance(instance)}.json"


def unit_path():
    return config_home() / "systemd" / "user" / UNIT_NAME


def instance_mapping(
    *, repository, repository_root, prefix, repository_config, observer,
    python, path, acknowledge_unguarded_preview,
):
    prefix = prefix.resolve()
    return {
        "schema": "excellent-nd/service-instance@v1",
        "repository": repository,
        "repository_root": str(repository_root.resolve()),
        "workflow": str(prefix / "WORKFLOW.md"),
        "symphony": str(prefix / "symphony"),
        "host_config": str(prefix / "host.json"),
        "repository_config": str(repository_config.resolve()),
        "observer": str(observer.resolve()),
        "python": str(python.resolve()),
        "path": path,
        "acknowledge_unguarded_preview": bool(acknowledge_unguarded_preview),
    }


def write_instance_mapping(path, mapping):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    with lock_path.open("a+") as lock:
        lock_path.chmod(0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        if path.exists():
            current = json.loads(path.read_text(encoding="utf-8"))
            identity = ("repository", "repository_root")
            if any(current.get(key) != mapping.get(key) for key in identity):
                raise ValueError(f"service instance {path.stem!r} already maps to another repository")
        with tempfile.NamedTemporaryFile("w", dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
            json.dump(mapping, stream, indent=2, sort_keys=True)
            stream.write("\n")
            temporary = Path(stream.name)
        temporary.chmod(0o600)
        temporary.replace(path)


def _unit_quote(path):
    return '"' + str(path).replace("%", "%%").replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_unit(template, python, runner):
    return template.replace("__PYTHON__", _unit_quote(python)).replace("__RUNNER__", _unit_quote(runner))


def install(instance, mapping, template, python, runner):
    instance = validate_instance(instance)
    write_instance_mapping(mapping_path(instance), mapping)
    destination = unit_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_unit(template.read_text(encoding="utf-8"), python, runner)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(destination)
    return f"excellent-nd@{instance}.service"


def systemctl(*args):
    return subprocess.run(
        ["systemctl", "--user", *args], check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    ).stdout.strip()


def _descendant_pids(root_pid):
    descendants = {root_pid}
    changed = True
    while changed:
        changed = False
        for status in Path("/proc").glob("[0-9]*/status"):
            try:
                fields = dict(
                    line.split(":", 1) for line in status.read_text(errors="replace").splitlines()
                    if ":" in line
                )
                pid = int(fields["Pid"].strip())
                parent = int(fields["PPid"].strip())
            except (OSError, KeyError, ValueError):
                continue
            if parent in descendants and pid not in descendants:
                descendants.add(pid)
                changed = True
    return descendants


def process_tree_matches(commands, main_pid, observer, symphony):
    expected_observer = str(observer.resolve()).encode()
    expected_symphony = str(symphony.resolve()).encode()
    return expected_observer in commands.get(main_pid, b"") and any(
        pid != main_pid and (expected_symphony in command or b"symphony" in command.lower())
        for pid, command in commands.items()
    )


def verify_process_tree(service, observer, symphony, attempts=10):
    for _ in range(attempts):
        main_pid = int(systemctl("show", service, "--property=MainPID", "--value") or "0")
        commands = {}
        for pid in _descendant_pids(main_pid) if main_pid else ():
            try:
                commands[pid] = (Path("/proc") / str(pid) / "cmdline").read_bytes()
            except OSError:
                pass
        if process_tree_matches(commands, main_pid, observer, symphony):
            return
        time.sleep(1)
    raise RuntimeError(f"{service} is active but observer/Symphony process tree is incomplete")


def enable_and_start(service, observer, symphony):
    systemctl("daemon-reload")
    try:
        systemctl("restart", service)
        if systemctl("is-active", service) != "active":
            raise RuntimeError(f"{service} did not become active")
        verify_process_tree(service, observer, symphony)
    except Exception:
        systemctl("stop", service)
        systemctl("disable", service)
        raise
    systemctl("enable", service)
