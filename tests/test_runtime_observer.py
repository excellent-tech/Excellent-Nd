import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts.repository_config import default_config
from scripts.runtime_observer import (
    GitHub,
    MARKER_FILENAME,
    apply_hook_transition,
    apply_transition_marker,
    classify_interruption,
    clear_applied_marker,
    decode_transition_event,
    encode_transition_event,
    extract_context,
    next_labels,
    prepare_workspace,
    runtime_event_for,
    sanitize,
    set_workflow_status,
    symphony_command,
    worker_started_issue,
    workspace_decision,
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


class RecordingGitHub(GitHub):
    def __init__(self, config, labels=None):
        self.repo = "owner/sample-app"
        self.config = config
        self.token = "not-used"
        self.calls = []
        self.labels = labels or ["symphony-ready"]

    def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        if method == "GET":
            return {
                "body": '{"workflow_status": "scheduled"}',
                "labels": [{"name": label} for label in self.labels],
            }
        return {}


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
        self.assertEqual(
            next_labels(["bug"], "running", config),
            ["bug", "symphony-ready"],
        )

    def test_runtime_event_mapping_does_not_change_core_statuses(self):
        self.assertEqual(runtime_event_for("blocked", "decision"), "decision_required")
        self.assertEqual(runtime_event_for("blocked", "external"), "external_blocked")
        self.assertEqual(runtime_event_for("failed", "external"), "execution_failed")
        self.assertEqual(runtime_event_for("review", "external"), "review_ready")
        self.assertEqual(runtime_event_for("running", "external"), "execution_started")
        self.assertIsNone(runtime_event_for("scheduled", "external"))

    def test_worker_start_requires_the_observed_symphony_event(self):
        self.assertEqual(
            worker_started_issue(
                "Starting worker attempt for issue_id=42 issue_identifier=GH-42"
            ),
            42,
        )
        for line in (
            "Dispatching issue to agent: issue_id=42 issue_identifier=GH-42",
            "Running workspace hook hook=before_run issue_identifier=GH-42",
            "Codex session started issue_identifier=GH-42",
            "starting worker attempt for issue_identifier=GH-42",
        ):
            with self.subTest(line=line):
                self.assertIsNone(worker_started_issue(line))

    @patch("scripts.runtime_observer.transition_event")
    def test_running_transition_restores_routing_only_after_project_update(self, update):
        github = RecordingGitHub(github_project_config())

        github.transition(42, "running", "worker started")

        patches = [call for call in github.calls if call[0] == "PATCH"]
        first_patch, body_patch, final_patch = patches
        self.assertEqual(first_patch[0:2], ("PATCH", "/issues/42"))
        self.assertNotIn("symphony-ready", first_patch[2]["labels"])
        self.assertNotIn("body", first_patch[2])
        self.assertIn("body", body_patch[2])
        self.assertNotIn("labels", body_patch[2])
        update.assert_called_once_with("owner/sample-app", 42, "execution_started", github.config)
        self.assertIn("symphony-ready", final_patch[2]["labels"])
        self.assertEqual(github.calls[-1][0:2], ("PATCH", "/issues/42"))

    def test_label_authority_changes_only_routing_in_first_patch(self):
        github = RecordingGitHub(
            self.config,
            labels=["bug", "symphony-ready", "nd-status:scheduled"],
        )

        github.transition(42, "running", "worker started")

        patches = [call for call in github.calls if call[0] == "PATCH"]
        self.assertEqual(
            patches[0][2],
            {"labels": ["bug", "nd-status:scheduled"]},
        )
        self.assertEqual(
            patches[-1][2],
            {"labels": ["bug", "symphony-ready", "nd-status:running"]},
        )

    @patch("scripts.runtime_observer.transition_event", side_effect=RuntimeError("project unavailable"))
    def test_project_failure_keeps_routing_off_and_records_mismatch(self, _update):
        github = RecordingGitHub(github_project_config())

        with self.assertRaisesRegex(RuntimeError, "project unavailable"):
            github.transition(42, "running", "worker started")

        patches = [call for call in github.calls if call[0] == "PATCH"]
        self.assertEqual(len(patches), 2)
        self.assertNotIn("symphony-ready", patches[0][2]["labels"])
        self.assertNotIn("labels", patches[1][2])
        self.assertIn("transition incomplete", github.calls[-1][2]["body"].lower())

    def test_structured_transition_event_round_trips(self):
        event = {
            "schema": "excellent-nd/runtime-transition@v1",
            "issue": 42,
            "run_id": "run-123",
            "attempt": "1",
            "transition": "blocked",
            "block_kind": "external",
            "reason": "base drift",
        }
        self.assertEqual(decode_transition_event(encode_transition_event(event)), event)

    def test_marker_application_is_idempotent(self):
        github = Mock()
        github.repo = "owner/sample-app"
        marker = {
            "schema": "excellent-nd/runtime-transition@v1",
            "run_id": "run-123",
            "attempt": "1",
            "transition": "review",
            "reason": "verification passed",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker_path = root / MARKER_FILENAME
            receipts = root / "receipts"
            marker_path.parent.mkdir(parents=True)
            marker_path.write_text(json.dumps(marker), encoding="utf-8")
            self.assertEqual(
                apply_transition_marker(github, 42, marker_path, receipts),
                "applied",
            )
            self.assertEqual(
                apply_transition_marker(github, 42, marker_path, receipts),
                "duplicate",
            )
            self.assertTrue(marker_path.exists())
            self.assertTrue(
                clear_applied_marker(
                    marker_path,
                    receipts,
                    "owner/sample-app",
                    42,
                )
            )
            self.assertFalse(marker_path.exists())

    def test_unbound_or_corrupt_receipt_tombstone_fails_closed(self):
        for corrupt in ("not json", "[]", "null"):
            with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as temporary:
                github = Mock()
                github.repo = "owner/sample-app"
                root = Path(temporary)
                marker_path = root / MARKER_FILENAME
                receipts = root / "receipts"
                marker_path.parent.mkdir(parents=True)
                receipts.mkdir()
                receipt = receipts / ("a" * 64 + ".json")
                receipt.write_text(corrupt, encoding="utf-8")
                marker_path.write_text(json.dumps({
                    "schema": "excellent-nd/runtime-transition-receipt@v1",
                    "receipt": receipt.name,
                }), encoding="utf-8")

                self.assertEqual(
                    apply_transition_marker(github, 42, marker_path, receipts),
                    "blocked",
                )
                self.assertFalse(
                    clear_applied_marker(
                        marker_path,
                        receipts,
                        "owner/sample-app",
                        42,
                    )
                )
        github.transition.assert_called_once()

    def test_missing_corrupt_and_unknown_markers_fail_closed(self):
        invalid_values = (
            None,
            "not json",
            json.dumps({
                "schema": "excellent-nd/runtime-transition@v1",
                "run_id": "run-123",
                "attempt": "1",
                "transition": "invented",
                "reason": "do not guess",
            }),
        )
        for value in invalid_values:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                marker_path = root / MARKER_FILENAME
                if value is not None:
                    marker_path.parent.mkdir(parents=True)
                    marker_path.write_text(value, encoding="utf-8")
                github = Mock()
                github.repo = "owner/sample-app"
                self.assertEqual(
                    apply_transition_marker(github, 42, marker_path, root / "receipts"),
                    "blocked",
                )
                args, kwargs = github.transition.call_args
                self.assertEqual(args[0:2], (42, "blocked"))
                self.assertEqual(kwargs["block_kind"], "external")

    def test_dirty_workspace_with_base_drift_stops_before_codex(self):
        self.assertEqual(workspace_decision("?? draft.md\n", "a" * 40, "b" * 40), "block")
        self.assertEqual(workspace_decision("?? draft.md\n", "b" * 40, "b" * 40), "continue")
        self.assertEqual(workspace_decision("", "a" * 40, "b" * 40), "refresh")

    @patch("scripts.runtime_observer.command")
    def test_dirty_base_drift_produces_blocker_without_reset(self, run):
        run.side_effect = ["?? draft.md", "main", "", "a" * 40, "b" * 40]
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary) / "GH-42"
            workspace.mkdir()
            event = prepare_workspace("owner/sample-app", workspace)

        self.assertEqual(event["issue"], 42)
        self.assertEqual(event["transition"], "blocked")
        self.assertIn("dirty workspace base drift", event["reason"])
        self.assertNotIn("draft.md", event["reason"])
        self.assertFalse(any(call.args[:2] == ("git", "reset") for call in run.call_args_list))

    def test_before_run_blocker_uses_structured_hook_output(self):
        github = Mock()
        event = {
            "schema": "excellent-nd/runtime-transition@v1",
            "issue": 42,
            "run_id": "workspace-preflight-old-new",
            "attempt": "before-run",
            "transition": "blocked",
            "block_kind": "external",
            "reason": "dirty workspace base drift",
        }
        line = (
            "Workspace hook failed hook=before_run issue_identifier=GH-42 output=\""
            + encode_transition_event(event)
            + "\""
        )

        self.assertEqual(
            apply_hook_transition(github, line, {"issue_number": 42}),
            "blocked",
        )
        args, kwargs = github.transition.call_args
        self.assertEqual(args[0:2], (42, "blocked"))
        self.assertEqual(kwargs["block_kind"], "external")

    def test_free_form_comment_text_is_not_a_transition_signal(self):
        github = Mock()
        self.assertIsNone(
            apply_hook_transition(
                github,
                "comment body says base drift issue_identifier=GH-42",
                {"issue_number": 42},
            )
        )
        github.transition.assert_not_called()

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
