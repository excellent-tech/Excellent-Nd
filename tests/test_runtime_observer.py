import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

RC_SPEC = importlib.util.spec_from_file_location("repository_config", SCRIPTS / "repository_config.py")
RC = importlib.util.module_from_spec(RC_SPEC)
assert RC_SPEC.loader is not None
RC_SPEC.loader.exec_module(RC)

SPEC = importlib.util.spec_from_file_location("runtime_observer", SCRIPTS / "runtime_observer.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RuntimeObserverTest(unittest.TestCase):
    def test_custom_labels_transition(self):
        config = RC.default_config()
        config["issue_integration"]["labels"]["routing"]["name"] = "ready-for-ai"
        config["issue_integration"]["labels"]["status"]["scheduled"]["name"] = "queued"
        config["issue_integration"]["labels"]["status"]["blocked"]["name"] = "hold"
        labels = ["bug", "ready-for-ai", "queued"]
        self.assertEqual(
            MODULE.next_labels(labels, "blocked", config),
            ["bug", "hold"],
        )
        self.assertEqual(
            MODULE.next_labels(["bug", "hold"], "scheduled", config),
            ["bug", "ready-for-ai", "queued"],
        )

    def test_sanitize_secret(self):
        self.assertNotIn("secret", MODULE.sanitize("TOKEN=secret"))


if __name__ == "__main__":
    unittest.main()
