import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location("repository_config", SCRIPTS / "repository_config.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def github_project_config():
    config = MODULE.default_config()
    integration = config["issue_integration"]
    integration["reviewed"]["project_fields"] = True
    integration["github_project"] = {"title": "Example Development"}
    integration["status_integration"] = {
        "authority": "github-project",
        "field": "Workflow Status",
        "event_mapping": {
            "execution_started": "In Progress",
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
            "field": "Workflow Status",
            "operator": "equals",
            "value": "Ready",
        }
    ]
    integration["labels"].pop("status", None)
    return config


class RepositoryConfigTest(unittest.TestCase):
    def test_default_config_is_valid_and_label_authority(self):
        config = MODULE.default_config()
        self.assertEqual(MODULE.routing_name(config), "symphony-ready")
        self.assertEqual(MODULE.target_prefix(config), "nd-target:")
        self.assertEqual(MODULE.status_authority(config), "labels")
        self.assertEqual(MODULE.dispatch_gates(config), [])

    def test_custom_existing_mapping_is_preserved(self):
        config = MODULE.default_config()
        config["issue_integration"]["labels"]["routing"] = {
            "name": "ready-for-ai",
            "management": "existing",
        }
        config["issue_integration"]["labels"]["status"]["running"] = {
            "name": "in-progress",
            "management": "existing",
        }
        MODULE.validate_config(config)
        actions = MODULE.plan_label_actions(
            config,
            "worker-a",
            {"ready-for-ai", "in-progress"},
        )
        by_role = {item["role"]: item for item in actions}
        self.assertEqual(by_role["routing"]["action"], "preserve")
        self.assertEqual(by_role["running"]["action"], "preserve")
        self.assertEqual(by_role["scheduled"]["action"], "create")

    def test_missing_existing_managed_label_fails_closed(self):
        config = MODULE.default_config()
        config["issue_integration"]["labels"]["routing"] = {
            "name": "ready-for-ai",
            "management": "existing",
        }
        with self.assertRaisesRegex(ValueError, "required existing label is missing"):
            MODULE.plan_label_actions(config, "worker-a", set())

    def test_duplicate_semantic_label_is_rejected(self):
        config = MODULE.default_config()
        config["issue_integration"]["labels"]["status"]["review"]["name"] = "symphony-ready"
        with self.assertRaisesRegex(ValueError, "distinct label names"):
            MODULE.validate_config(config)

    def test_unreviewed_repository_is_rejected(self):
        config = MODULE.default_config()
        config["issue_integration"]["reviewed"]["automation"] = False
        with self.assertRaisesRegex(ValueError, "reviewed.automation"):
            MODULE.validate_config(config)

    def test_github_project_authority_disables_status_labels(self):
        config = github_project_config()
        MODULE.validate_config(config)
        self.assertEqual(MODULE.status_authority(config), "github-project")
        self.assertEqual(MODULE.status_names(config), set())
        roles = [item["role"] for item in MODULE.label_specs(config, "worker-a")]
        self.assertEqual(roles, ["routing", "target"])
        self.assertEqual(
            MODULE.project_event_value(config, "review_ready"),
            "Review",
        )

    def test_project_fields_are_not_hard_coded(self):
        config = github_project_config()
        gates = config["issue_integration"]["dispatch_gates"]
        gates[:] = [{
            "id": "only-status",
            "source": "github-project-field",
            "field": "Custom Workflow",
            "operator": "in",
            "values": ["Ready", "Queued"],
        }]
        config["issue_integration"]["status_integration"]["field"] = "Custom Workflow"
        MODULE.validate_config(config)

    def test_project_fields_require_review(self):
        config = github_project_config()
        config["issue_integration"]["reviewed"]["project_fields"] = False
        with self.assertRaisesRegex(ValueError, "reviewed.project_fields"):
            MODULE.validate_config(config)

    def test_label_authority_can_still_use_project_gate(self):
        config = MODULE.default_config()
        integration = config["issue_integration"]
        integration["reviewed"]["project_fields"] = True
        integration["github_project"] = {"title": "Release Board"}
        integration["dispatch_gates"] = [{
            "id": "release-approved",
            "source": "github-project-field",
            "field": "Release Gate",
            "operator": "equals",
            "value": "Approved",
        }]
        MODULE.validate_config(config)
        self.assertEqual(MODULE.status_authority(config), "labels")
        self.assertTrue(MODULE.uses_github_project(config))

    def test_duplicate_gate_id_is_rejected(self):
        config = github_project_config()
        gate = config["issue_integration"]["dispatch_gates"][0]
        config["issue_integration"]["dispatch_gates"].append(dict(gate))
        with self.assertRaisesRegex(ValueError, "duplicate dispatch gate id"):
            MODULE.validate_config(config)

    def test_mutable_event_requires_mapping(self):
        config = github_project_config()
        del config["issue_integration"]["status_integration"]["event_mapping"]["review_ready"]
        with self.assertRaisesRegex(ValueError, "require event_mapping"):
            MODULE.validate_config(config)


if __name__ == "__main__":
    unittest.main()
