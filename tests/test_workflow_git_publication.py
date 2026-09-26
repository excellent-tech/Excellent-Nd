import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "config" / "WORKFLOW.md.tpl"


class WorkflowGitPublicationTests(unittest.TestCase):
    def setUp(self):
        self.workflow = TEMPLATE.read_text(encoding="utf-8")

    def test_clean_workspace_is_refreshed_outside_codex_sandbox(self):
        self.assertIn("before_run:", self.workflow)
        self.assertIn("git fetch --prune origin", self.workflow)
        self.assertIn('git reset --hard "origin/$default_branch"', self.workflow)

    def test_workspace_write_uses_host_side_github_api_for_publication(self):
        self.assertIn("thread_sandbox: workspace-write", self.workflow)
        self.assertIn("github_api", self.workflow)
        self.assertIn("Git Data REST API", self.workflow)
        self.assertNotIn("thread_sandbox: danger-full-access", self.workflow)


if __name__ == "__main__":
    unittest.main()
