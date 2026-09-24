import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location("excellent_nd_setup", SCRIPTS / "setup.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SetupImportTest(unittest.TestCase):
    def test_target_inventory_writer_is_available(self):
        self.assertTrue(callable(MODULE.write_target_record))


if __name__ == "__main__":
    unittest.main()
