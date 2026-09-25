import copy
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


class RepositoryConfigTest(unittest.TestCase):
    def test_default_config_is_valid(self):
        config = MODULE.default_config()
        self.assertEqual(MODULE.routing_name(config), "symphony-ready")
        self.assertEqual(MODULE.target_prefix(config), "nd-target:")

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


if __name__ == "__main__":
    unittest.main()
