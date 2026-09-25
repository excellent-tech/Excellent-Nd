import unittest

from scripts.repository_adapter import (
    evaluate_gates,
    preflight,
    resolve_context,
    transition_event,
)
from scripts.repository_config import default_config


def config():
    value = default_config()
    integration = value["issue_integration"]
    integration["reviewed"]["project_fields"] = True
    integration["github_project"] = {"title": "Example Development"}
    integration["status_integration"] = {
        "authority": "github-project",
        "field": "Status",
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
    integration["dispatch_gates"] = [
        {
            "id": "ready",
            "source": "github-project-field",
            "field": "Status",
            "operator": "equals",
            "value": "Ready",
        },
        {
            "id": "worker",
            "source": "github-project-field",
            "field": "Executor",
            "operator": "equals",
            "value": "Codex",
        },
        {
            "id": "approval",
            "source": "github-project-field",
            "field": "Approval",
            "operator": "in",
            "values": ["No", "Approved"],
        },
        {
            "id": "blockers",
            "source": "label",
            "operator": "absent",
            "values": ["blocked", "decision-needed"],
        },
        {
            "id": "open",
            "source": "issue-state",
            "operator": "equals",
            "value": "open",
        },
    ]
    integration["labels"].pop("status", None)
    return value


def field_node(name, value, options=None, field_id=None):
    options = options or [{"id": f"{name}-value", "name": value}]
    return {
        "name": value,
        "optionId": "current",
        "field": {
            "id": field_id or f"FIELD_{name.upper().replace(' ', '_')}",
            "name": name,
            "options": options,
        },
    }


def snapshot(
    status="Ready",
    executor="Codex",
    approval="Approved",
    labels=None,
    issue_state="OPEN",
    project_title="Example Development",
    labels_next=False,
    project_items_next=False,
    fields_next=False,
):
    labels = labels or []
    status_options = [
        {"id": "s-ready", "name": "Ready"},
        {"id": "s-working", "name": "Working"},
        {"id": "s-decision", "name": "Needs Decision"},
        {"id": "s-hold", "name": "On Hold"},
        {"id": "s-review", "name": "Review"},
    ]
    return {
        "data": {
            "repository": {
                "issue": {
                    "number": 21,
                    "state": issue_state,
                    "labels": {
                        "nodes": [{"name": name} for name in labels],
                        "pageInfo": {"hasNextPage": labels_next},
                    },
                    "projectItems": {
                        "nodes": [{
                            "id": "ITEM1",
                            "project": {
                                "id": "PROJECT1",
                                "title": project_title,
                                "number": 1,
                            },
                            "fieldValues": {
                                "nodes": [
                                    field_node("Status", status, status_options, "FIELD_STATUS"),
                                    field_node("Executor", executor),
                                    field_node("Approval", approval),
                                ],
                                "pageInfo": {"hasNextPage": fields_next},
                            },
                        }],
                        "pageInfo": {"hasNextPage": project_items_next},
                    },
                }
            }
        }
    }


class RepositoryAdapterTest(unittest.TestCase):
    def test_generic_gates_pass_without_hard_coded_field_names(self):
        result = evaluate_gates(resolve_context(snapshot(), config()), config())
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["observed"]["worker"], "Codex")

    def test_stops_on_each_repository_defined_gate(self):
        result = evaluate_gates(
            resolve_context(
                snapshot(
                    status="Backlog",
                    executor="Human",
                    approval="Required",
                    labels=["blocked"],
                    issue_state="CLOSED",
                ),
                config(),
            ),
            config(),
        )
        self.assertEqual(result["result"], "STOP")
        self.assertGreaterEqual(len(result["reasons"]), 5)

    def test_unknown_project_field_never_passes_not_equals(self):
        cfg = config()
        cfg["issue_integration"]["dispatch_gates"] = [{
            "id": "optional-looking-but-required",
            "source": "github-project-field",
            "field": "Missing",
            "operator": "not-equals",
            "value": "Denied",
        }]
        result = evaluate_gates(resolve_context(snapshot(), cfg), cfg)
        self.assertEqual(result["result"], "STOP")
        self.assertIn("unavailable", result["reasons"][0])

    def test_missing_or_multiple_project_item_fails_closed(self):
        missing = snapshot()
        missing["data"]["repository"]["issue"]["projectItems"]["nodes"] = []
        with self.assertRaisesRegex(ValueError, "expected exactly one"):
            resolve_context(missing, config())

        duplicate = snapshot()
        duplicate["data"]["repository"]["issue"]["projectItems"]["nodes"].append(
            duplicate["data"]["repository"]["issue"]["projectItems"]["nodes"][0].copy()
        )
        with self.assertRaisesRegex(ValueError, "expected exactly one"):
            resolve_context(duplicate, config())

    def test_pagination_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "project item list is paginated"):
            resolve_context(snapshot(project_items_next=True), config())
        with self.assertRaisesRegex(ValueError, "field values are paginated"):
            resolve_context(snapshot(fields_next=True), config())

        ctx = resolve_context(snapshot(labels_next=True), config())
        result = evaluate_gates(ctx, config())
        self.assertEqual(result["result"], "STOP")
        self.assertTrue(any("label list is paginated" in reason for reason in result["reasons"]))

    def test_preflight_uses_graphql_snapshot(self):
        calls = []
        def runner(args):
            calls.append(args)
            return snapshot()
        result = preflight("excellent-tech/example", 21, config(), runner)
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(calls)

    def test_transition_event_uses_repository_mapping(self):
        calls = []
        def runner(args):
            calls.append(args)
            if len(calls) == 1:
                return snapshot()
            return {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "ITEM1"}}}}

        result = transition_event(
            "excellent-tech/example",
            21,
            "review_ready",
            config(),
            runner,
        )
        self.assertEqual(result["value"], "Review")
        joined = " ".join(calls[1])
        self.assertIn("FIELD_STATUS", joined)
        self.assertIn("s-review", joined)

    def test_unenabled_event_is_rejected(self):
        cfg = config()
        cfg["issue_integration"]["status_integration"]["mutable_events"].remove("review_ready")
        with self.assertRaisesRegex(ValueError, "not enabled"):
            transition_event(
                "excellent-tech/example",
                21,
                "review_ready",
                cfg,
                lambda args: snapshot(),
            )

    def test_label_only_gates_do_not_require_project_fields(self):
        cfg = default_config()
        cfg["issue_integration"]["dispatch_gates"] = [{
            "id": "not-blocked",
            "source": "label",
            "operator": "absent",
            "values": ["blocked"],
        }]
        snap = snapshot()
        snap["data"]["repository"]["issue"]["projectItems"] = {
            "nodes": [],
            "pageInfo": {"hasNextPage": False},
        }
        ctx = resolve_context(snap, cfg)
        self.assertEqual(evaluate_gates(ctx, cfg)["result"], "PASS")


if __name__ == "__main__":
    unittest.main()
