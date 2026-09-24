import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "target_inventory", ROOT / "scripts" / "target_inventory.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class TargetInventoryTest(unittest.TestCase):
    def test_one_host_one_file_and_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = MODULE.write_target_record(
                root,
                execution_target="worker-a",
                hostname="worker-a",
                enabled=True,
                max_concurrent_agents=1,
                verified_at="2026-09-24T00:00:00Z",
            )
            self.assertEqual(path, root / ".excellent-nd/targets/worker-a.json")
            records = MODULE.load_targets(root)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["id"], "worker-a")
            self.assertEqual(records[0]["routing_label"], "nd-target:worker-a")
            self.assertEqual(records[0]["hostname"], "worker-a")

    def test_alias_can_omit_hostname(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = MODULE.write_target_record(
                root,
                execution_target="public-worker-01",
                hostname=None,
                enabled=True,
                max_concurrent_agents=2,
                verified_at="2026-09-24T00:00:00Z",
            )
            record = json.loads(path.read_text())
            self.assertIsNone(record["hostname"])

    def test_rejects_arbitrary_or_secret_fields(self):
        record = {
            "schema": MODULE.SCHEMA,
            "id": "worker-a",
            "hostname": "worker-a",
            "enabled": True,
            "routing_label": "nd-target:worker-a",
            "max_concurrent_agents": 1,
            "last_verified_at": "2026-09-24T00:00:00Z",
            "token": "must-not-be-stored",
        }
        with self.assertRaises(ValueError):
            MODULE.validate_record(record)


if __name__ == "__main__":
    unittest.main()
