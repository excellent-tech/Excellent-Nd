import unittest
from types import SimpleNamespace

from scripts.repository_config import default_config
from scripts.runtime_observer import (
    GitHub,
    classify_interruption,
    extract_context,
    next_labels,
    runtime_event_for,
    sanitize,
    set_workflow_status,
    symphony_command,
    SYMPHONY_ACK_FLAG,
)


def github_project_config():
    config = default_config()
    integration = config["issue_integration"]
    integration["reviewed"]["project_fields"] = True
    integration["github_project"] = {"title": "Example Development"}
    integration["status_integration"] = {
        "authority": "github-project",
        "field": "Workflow",
        "event_mapping": {
            "execution_started": "Working",
            "decision_required": "Needs Decision",
            "external_blocked": "On Hold",
            "review_ready": "Review",
            "execution_failed": "On Hold",
        },
        "mutable_events": [
            "execution_started",
            "decision_required",
            "external_blocked",
            "review_ready",
            "execution_failed",
        ],
    }
    integration["dispatch_gates"] = [{
        "id": "ready",
        "source": "github-project-field",
        "field": "Workflow",
        "operator": "equals",
        "value": "Ready",
    }]
    integration["labels"].pop("status", None)
    return config


class ObserverTest(unittest.TestCase):
    def setUp(self):
        self.config = default_config()

    def test_non_transient_usage_limit_is_blocking(self):
        self.assertEqual(
            classify_interruption("account usage limit reached; reset_at=2026-09-22T00:00:00Z"),
            "usage_limit",
        )
        self.assertIsNone(classify_interruption("tracker rate limited; retry_after=30"))
        self.assertEqual(
            classify_interruption("tracker rate limit issue_identifier=GH-6 retry_after=7200"),
            "usage_limit",
        )

    def test_failure_categories(self):
        self.assertEqual(classify_interruption("turn timeout issue_identifier=GH-6"), "turn_timeout")
        self.assertEqual(
            classify_interruption("thread/start failed: app server startup error issue_identifier=GH-6"),
            "app_server_startup",
        )
        self.assertEqual(
            classify_interruption("agent abnormal exit issue_identifier=GH-6"),
            "agent_abnormal_exit",
        )

    def test_context_uses_only_public_safe_identifiers(self):
        context = extract_context(
            "issue_identifier=GH-42 session_id=abc-123 attempt=7 retry_after=7200"
        )
        self.assertEqual(context["issue_number"], 42)
        self.assertEqual(context["session_id"], "abc-123")
        self.assertEqual(context["attempt"], "7")
        self.assertEqual(context["retry_after"], "7200")

    def test_sanitize_removes_secrets_and_private_paths(self):
        value = sanitize(
            "GITHUB_TOKEN=secret github_pat_abcdefghijklmnopqrstuvwxyz /home/alice/private "
            "https://user:pass@example.invalid/repo"
        )
        self.assertNotIn("secret", value)
        self.assertNotIn("github_pat_", value)
        self.assertNotIn("/home/alice", value)
        self.assertNotIn("user:pass", value)

    def test_standard_status_and_labels_change_together(self):
        body = '{"workflow_status": "running"}'
        self.assertEqual(set_workflow_status(body, "blocked"), '{"workflow_status": "blocked"}')
        self.assertEqual(
            next_labels(["bug", "symphony-ready", "nd-status:running"], "blocked", self.config),
            ["bug", "nd-status:blocked"],
        )
        self.assertEqual(
            next_labels(["bug", "nd-status:blocked"], "scheduled", self.config),
            ["bug", "symphony-ready", "nd-status:scheduled"],
        )

    def test_github_project_authority_never_adds_status_labels(self):
        config = github_project_config()
        self.assertEqual(
            next_labels(["bug", "symphony-ready", "blocked"], "review", config),
            ["bug", "blocked"],
        )
        self.assertEqual(
            next_labels(["bug"], "scheduled", config),
            ["bug", "symphony-ready"],
        )

    def test_runtime_event_mapping_does_not_change_core_statuses(self):
        self.assertEqual(runtime_event_for("blocked", "decision"), "decision_required")
        self.assertEqual(runtime_event_for("blocked", "external"), "external_blocked")
        self.assertEqual(runtime_event_for("failed", "external"), "execution_failed")
        self.assertEqual(runtime_event_for("review", "external"), "review_ready")
        self.assertIsNone(runtime_event_for("scheduled", "external"))

    def test_repository_input_is_validated(self):
        with self.assertRaises(ValueError):
            GitHub("../invalid", self.config, token="not-used")

    def test_symphony_preview_acknowledgement_is_explicit(self):
        args = SimpleNamespace(
            symphony="/tmp/symphony",
            workflow="/tmp/WORKFLOW.md",
            acknowledge_unguarded_preview=False,
        )
        self.assertEqual(
            symphony_command(args),
            ["/tmp/symphony", "/tmp/WORKFLOW.md"],
        )

        args.acknowledge_unguarded_preview = True
        self.assertEqual(
            symphony_command(args),
            ["/tmp/symphony", SYMPHONY_ACK_FLAG, "/tmp/WORKFLOW.md"],
        )


if __name__ == "__main__":
    unittest.main()
