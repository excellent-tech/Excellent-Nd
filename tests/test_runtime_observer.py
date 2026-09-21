import unittest

from scripts.runtime_observer import (
    GitHub,
    classify_interruption,
    extract_context,
    next_labels,
    sanitize,
    set_workflow_status,
)


class ObserverTest(unittest.TestCase):
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

    def test_status_and_labels_change_together(self):
        body = '{"workflow_status": "running"}'
        self.assertEqual(set_workflow_status(body, "blocked"), '{"workflow_status": "blocked"}')
        self.assertEqual(
            next_labels(["bug", "symphony-ready", "nd-status:running"], "blocked"),
            ["bug", "nd-status:blocked"],
        )
        self.assertEqual(
            next_labels(["bug", "nd-status:blocked"], "scheduled"),
            ["bug", "symphony-ready", "nd-status:scheduled"],
        )

    def test_repository_input_is_validated(self):
        with self.assertRaises(ValueError):
            GitHub("../invalid", token="not-used")

    def test_review_also_removes_routing(self):
        self.assertEqual(
            next_labels(["symphony-ready", "nd-status:running"], "review"),
            ["nd-status:review"],
        )


if __name__ == "__main__":
    unittest.main()
