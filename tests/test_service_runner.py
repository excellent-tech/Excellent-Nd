import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import service_runner


class ServiceRunnerTest(unittest.TestCase):
    def test_mapping_requires_exact_schema_and_boolean_acknowledgement(self):
        mapping = {
            "schema": "excellent-nd/service-instance@v1",
            "repository": "example-org/sample-app",
            "repository_root": "/srv/sample-app",
            "workflow": "/srv/sample-app/.excellent-nd/WORKFLOW.md",
            "symphony": "/srv/sample-app/.excellent-nd/symphony",
            "host_config": "/srv/sample-app/.excellent-nd/host.json",
            "repository_config": "/srv/sample-app/.excellent-nd/repository.json",
            "observer": "/opt/excellent-nd/scripts/runtime_observer.py",
            "python": "/usr/bin/python3",
            "path": "/usr/bin",
            "acknowledge_unguarded_preview": "false",
        }

        with self.assertRaisesRegex(RuntimeError, "invalid service instance mapping"):
            service_runner.validate_mapping(mapping)

    def test_command_uses_repository_specific_paths_and_acknowledgement(self):
        mapping = {
            "repository": "example-org/sample-app",
            "repository_root": "/srv/sample-app",
            "workflow": "/srv/sample-app/.excellent-nd/WORKFLOW.md",
            "symphony": "/srv/sample-app/.excellent-nd/symphony",
            "host_config": "/srv/sample-app/.excellent-nd/host.json",
            "repository_config": "/srv/sample-app/.excellent-nd/repository.json",
            "observer": "/opt/excellent-nd/scripts/runtime_observer.py",
            "python": "/usr/bin/python3",
            "path": "/usr/local/bin:/usr/bin",
            "acknowledge_unguarded_preview": True,
        }

        self.assertEqual(
            service_runner.observer_command(mapping),
            [
                "/usr/bin/python3",
                "/opt/excellent-nd/scripts/runtime_observer.py",
                "run",
                "--repo",
                "example-org/sample-app",
                "--workflow",
                "/srv/sample-app/.excellent-nd/WORKFLOW.md",
                "--symphony",
                "/srv/sample-app/.excellent-nd/symphony",
                "--i-understand-that-this-will-be-running-without-the-usual-guardrails",
                "--repository-config",
                "/srv/sample-app/.excellent-nd/repository.json",
            ],
        )

    def test_run_gets_token_at_start_without_persisting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "sample-app"
            runtime = root / ".excellent-nd"
            runtime.mkdir(parents=True)
            (root / ".git").mkdir()
            for path in (
                runtime / "WORKFLOW.md",
                runtime / "symphony",
                runtime / "repository.json",
                root / "observer.py",
            ):
                path.write_text("test")
            (runtime / "host.json").write_text(json.dumps({
                "repository": "example-org/sample-app",
            }))
            mapping_path = Path(directory) / "sample-app.json"
            mapping_path.write_text(json.dumps({
                "schema": "excellent-nd/service-instance@v1",
                "repository": "example-org/sample-app",
                "repository_root": str(root),
                "workflow": str(runtime / "WORKFLOW.md"),
                "symphony": str(runtime / "symphony"),
                "host_config": str(runtime / "host.json"),
                "repository_config": str(runtime / "repository.json"),
                "observer": str(root / "observer.py"),
                "python": "/usr/bin/python3",
                "path": "/usr/bin",
                "acknowledge_unguarded_preview": False,
            }))

            with mock.patch.object(service_runner, "mapping_path", return_value=mapping_path), \
                    mock.patch.object(service_runner.subprocess, "run") as run, \
                    mock.patch.object(service_runner.os, "execve") as execve:
                run.return_value = mock.Mock(stdout="secret-value\n")
                service_runner.run("sample-app")

            environment = execve.call_args.args[2]
            self.assertEqual(environment["GITHUB_TOKEN"], "secret-value")
            self.assertEqual(environment["PATH"], "/usr/bin")
            self.assertEqual(execve.call_args.args[0], "/usr/bin/python3")
            self.assertNotIn("secret-value", mapping_path.read_text())

    def test_credential_environment_rejects_empty_gh_token(self):
        with mock.patch.object(service_runner.subprocess, "run") as run:
            run.return_value = mock.Mock(stdout="\n")
            with self.assertRaisesRegex(RuntimeError, "empty credential"):
                service_runner.credential_environment("/usr/bin")


if __name__ == "__main__":
    unittest.main()
