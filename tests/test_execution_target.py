import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "execution_target", ROOT / "scripts" / "execution_target.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ExecutionTargetTest(unittest.TestCase):
    def test_normalize_and_label(self):
        self.assertEqual(MODULE.normalize_execution_target("Build-01"), "build-01")
        self.assertEqual(MODULE.routing_label("Build-01"), "nd-target:build-01")

    def test_rejects_unsafe_or_oversized_ids(self):
        for value in ("", "bad target", "bad/target", "-bad", "bad-", "a" * 41):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MODULE.normalize_execution_target(value)

    def test_label_fits_github_limit(self):
        target = "a" * MODULE.MAX_TARGET_ID_LENGTH
        self.assertEqual(len(MODULE.routing_label(target)), 50)

    def test_render_workflow_binds_repo_and_target(self):
        template = (
            'repo: "__REPOSITORY__"\n'
            "required_labels:\n"
            "  - symphony-ready\n"
            "  - __EXECUTION_TARGET_LABEL__\n"
        )
        rendered = MODULE.render_workflow(template, "owner/repo", "worker-a")
        self.assertIn('repo: "owner/repo"', rendered)
        self.assertIn("  - nd-target:worker-a", rendered)
        self.assertNotIn("__REPOSITORY__", rendered)
        self.assertNotIn("__EXECUTION_TARGET_LABEL__", rendered)


if __name__ == "__main__":
    unittest.main()
