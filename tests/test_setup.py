import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location("excellent_nd_setup", SCRIPTS / "setup.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SetupImportTest(unittest.TestCase):
    def test_required_helpers_are_available(self):
        self.assertTrue(callable(MODULE.write_target_record))
        self.assertTrue(callable(MODULE.load_repository_config))
        self.assertTrue(callable(MODULE.plan_label_actions))
        self.assertTrue(callable(MODULE.status_authority))

    def test_start_and_foreground_are_mutually_exclusive(self):
        parser = MODULE.argument_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "--repo", "example-org/sample-app",
                "--prefix", ".excellent-nd",
                "--skill-confirmed",
                "--start",
                "--foreground",
            ])

    def test_default_service_instance_is_repository_basename(self):
        self.assertEqual(MODULE.service_instance(None, Path("/srv/sample-app")), "sample-app")
        self.assertEqual(MODULE.service_instance("worker-a", Path("/srv/sample-app")), "worker-a")

    def test_start_fails_closed_outside_linux(self):
        with mock.patch.object(MODULE.platform, "system", return_value="Darwin"):
            with self.assertRaisesRegex(RuntimeError, "Linux"):
                MODULE.require_systemd_user()

    def test_runtime_prefix_is_resolved_from_repository_and_must_be_standard(self):
        root = Path("/srv/sample-app")
        self.assertEqual(MODULE.runtime_prefix(Path(".excellent-nd"), root), root / ".excellent-nd")
        with self.assertRaisesRegex(ValueError, "--prefix"):
            MODULE.runtime_prefix(Path("/tmp/runtime"), root)

    def test_foreground_injects_gh_credential_into_observer_environment(self):
        command = ["/usr/bin/python3", "/opt/excellent-nd/runtime_observer.py", "run"]
        environment = {"PATH": "/usr/bin", "GITHUB_TOKEN": "secret-value"}
        with mock.patch.object(MODULE, "credential_environment", return_value=environment), \
                mock.patch.object(MODULE.os, "execve") as execve:
            MODULE.run_foreground(command)
        execve.assert_called_once_with("/usr/bin/python3", command, environment)


if __name__ == "__main__":
    unittest.main()
