"""The host resume adapter must not mint authorization from task metadata."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import runtime_observer as observer
from scripts.repository_config import default_config


class DispatchAuthorizationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.config_path = Path(temporary.name) / "repository.json"
        self.config_path.write_text(json.dumps(default_config()), encoding="utf-8")
        self.calls = []
        self.issue = {
            "state": "open",
            "body": '```json\n{"schema":"excellent-nd/task@v1",'
                    '"plan_ref":"P-20261001-a1b2c3","task_ref":"T-002",'
                    '"workflow_status":"blocked","dispatch_scope":"plan",'
                    '"human_gate":"clear",'
                    '"dependencies":["https://github.com/owner/sample-app/issues/41"]}\n```',
            "labels": [{"name": "nd-target:worker-a"}],
        }

    def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        if method == "GET":
            return {"state": "closed"} if path.endswith("/41") else self.issue
        return {}

    def invoke(self, reason, *authorization):
        argv = [
            "resume", "--repo", "owner/sample-app", "--issue", "42",
            "--reason", reason, "--repository-config", str(self.config_path),
            *authorization,
        ]
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test-only"}), \
                patch.object(observer.GitHub, "request", self.request), \
                contextlib.redirect_stderr(io.StringIO()):
            return observer.main(argv)

    def assert_rejected_without_io(self, reason, *authorization):
        with self.assertRaises(SystemExit) as error:
            self.invoke(reason, *authorization)
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(self.calls, [])

    def test_explicit_selector_schedules_without_an_extra_approval_phrase(self):
        self.assertEqual(self.invoke("resume requested", "--explicit-mention"), 0)
        patches = [body for method, _path, body in self.calls if method == "PATCH"]
        updated = next(body["body"] for body in patches if "body" in body)
        self.assertIn('"workflow_status":"scheduled"', updated)
        self.assertNotIn("symphony-ready", patches[0]["labels"])
        self.assertIn("symphony-ready", patches[-1]["labels"])
        self.assertIn("nd-target:worker-a", patches[-1]["labels"])

    def test_natural_language_and_skill_selection_do_not_authorize_resume(self):
        for reason in ("execute now", "continue", "fetch results", "Skill auto-selected"):
            with self.subTest(reason=reason):
                self.assert_rejected_without_io(reason)

    def test_issue_plan_metadata_and_closed_dependency_do_not_authorize_resume(self):
        self.assert_rejected_without_io("existing Durable Task; dependency completed")

    def test_natural_language_authorization_flag_is_not_a_dispatch_path(self):
        self.assert_rejected_without_io("execute now", "--human-instruction")

    def test_plan_continuation_flag_is_not_a_dispatch_path(self):
        self.assert_rejected_without_io(
            "results ingested", "--plan-continuation", "--plan-ref", "P-20261001-a1b2c3",
        )


if __name__ == "__main__":
    unittest.main()
