import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from systemd_service import (
    instance_mapping,
    process_tree_matches,
    render_unit,
    validate_instance,
    write_instance_mapping,
)


class SystemdServiceTest(unittest.TestCase):
    def test_instance_mapping_keeps_repository_runtime_paths_separate(self):
        root = Path("/srv/sample-app")
        mapping = instance_mapping(
            repository="example-org/sample-app",
            repository_root=root,
            prefix=root / ".excellent-nd",
            repository_config=root / ".excellent-nd/repository.json",
            observer=Path("/opt/excellent-nd/scripts/runtime_observer.py"),
            python=Path("/usr/bin/python3"),
            path="/usr/local/bin:/usr/bin",
            acknowledge_unguarded_preview=True,
        )

        self.assertEqual(mapping["repository"], "example-org/sample-app")
        self.assertEqual(mapping["repository_root"], "/srv/sample-app")
        self.assertEqual(mapping["workflow"], "/srv/sample-app/.excellent-nd/WORKFLOW.md")
        self.assertEqual(mapping["symphony"], "/srv/sample-app/.excellent-nd/symphony")
        self.assertEqual(mapping["host_config"], "/srv/sample-app/.excellent-nd/host.json")
        self.assertEqual(mapping["repository_config"], "/srv/sample-app/.excellent-nd/repository.json")
        self.assertNotIn("token", json.dumps(mapping).lower())

    def test_unit_uses_instance_runner_without_credentials(self):
        template = "ExecStart=__PYTHON__ __RUNNER__ %i\nRestart=always\n"
        unit = render_unit(template, Path("/usr/bin/python3"), Path("/opt/excellent-nd/scripts/service_runner.py"))

        self.assertEqual(
            unit,
            'ExecStart="/usr/bin/python3" "/opt/excellent-nd/scripts/service_runner.py" %i\nRestart=always\n',
        )
        self.assertNotIn("GITHUB_TOKEN", unit)
        self.assertNotIn("token=", unit.lower())

    def test_unit_escapes_systemd_specifiers_in_paths(self):
        unit = render_unit(
            "ExecStart=__PYTHON__ __RUNNER__ %i\n",
            Path("/opt/100%/python3"),
            Path("/opt/100%/service_runner.py"),
        )
        self.assertEqual(unit, 'ExecStart="/opt/100%%/python3" "/opt/100%%/service_runner.py" %i\n')

    def test_rejects_unsafe_instance_names(self):
        for value in ("", "../sample-app", "sample/app", "sample app", "@sample", "a" * 81):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_instance(value)

    def test_existing_instance_for_another_repository_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample-app.json"
            path.write_text(json.dumps({"repository": "example-org/other", "repository_root": "/srv/other"}))

            with self.assertRaisesRegex(ValueError, "already maps to another repository"):
                write_instance_mapping(
                    path,
                    {"repository": "example-org/sample-app", "repository_root": "/srv/sample-app"},
                )

    def test_enable_start_checks_active_then_process_tree(self):
        calls = []

        def systemctl(*args):
            calls.append(args)
            return "active" if args[0] == "is-active" else ""

        with mock.patch("systemd_service.systemctl", side_effect=systemctl), \
                mock.patch("systemd_service.verify_process_tree") as verify:
            from systemd_service import enable_and_start
            enable_and_start(
                "excellent-nd@sample-app.service",
                Path("/opt/excellent-nd/scripts/runtime_observer.py"),
                Path("/srv/sample-app/.excellent-nd/symphony"),
            )

        self.assertEqual(calls, [
            ("daemon-reload",),
            ("restart", "excellent-nd@sample-app.service"),
            ("is-active", "excellent-nd@sample-app.service"),
            ("enable", "excellent-nd@sample-app.service"),
        ])
        verify.assert_called_once()

    def test_inactive_service_is_setup_failure(self):
        calls = []

        def systemctl(*args):
            calls.append(args)
            return "inactive" if args[0] == "is-active" else ""

        with mock.patch("systemd_service.systemctl", side_effect=systemctl):
            from systemd_service import enable_and_start
            with self.assertRaisesRegex(RuntimeError, "did not become active"):
                enable_and_start("excellent-nd@sample-app.service", Path("observer"), Path("symphony"))
        self.assertEqual(calls[-2:], [
            ("stop", "excellent-nd@sample-app.service"),
            ("disable", "excellent-nd@sample-app.service"),
        ])

    def test_steady_state_burrito_process_counts_as_symphony_child(self):
        commands = {
            100: b"/usr/bin/python3\0/opt/excellent-nd/runtime_observer.py\0run\0",
            101: b"/home/worker/.local/share/.burrito/symphony_erts/erts/bin/beam.smp\0",
        }

        self.assertTrue(process_tree_matches(
            commands,
            100,
            Path("/opt/excellent-nd/runtime_observer.py"),
            Path("/srv/sample-app/.excellent-nd/symphony"),
        ))


if __name__ == "__main__":
    unittest.main()
