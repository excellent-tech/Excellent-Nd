import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_plugin_package", ROOT / "scripts" / "build_plugin_package.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PluginPackageTest(unittest.TestCase):
    def test_manifest_and_marketplace(self):
        manifest = MODULE.validate_source(ROOT)
        self.assertEqual(manifest["name"], "excellent-nd")
        self.assertEqual(manifest["version"], "1.0.2")

        marketplace = json.loads(
            (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
        )
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "excellent-nd")
        self.assertEqual(entry["source"]["source"], "local")
        self.assertEqual(entry["source"]["path"], "./")
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")

    def test_build_is_deterministic_and_skill_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.zip"
            second = Path(tmp) / "second.zip"
            digest1 = MODULE.build_package(ROOT, first)
            digest2 = MODULE.build_package(ROOT, second)
            self.assertEqual(digest1, digest2)
            self.assertEqual(
                digest1, hashlib.sha256(first.read_bytes()).hexdigest()
            )

            with zipfile.ZipFile(first) as archive:
                names = set(archive.namelist())

            required = {
                "plugin.json",
                "skills/excellent-nd/SKILL.md",
                "skills/excellent-nd/references/repository-onboarding.md",
                "scripts/setup.py",
                "scripts/execution_target.py",
                "scripts/repository_config.py",
                "scripts/repository_adapter.py",
                "scripts/project_adapter.py",
                "scripts/target_inventory.py",
                "config/WORKFLOW.md.tpl",
                "config/repository-config.default.json",
                "config/repository-config.github-project.example.json",
                "config/runtime-lock.json",
            }
            self.assertTrue(required.issubset(names), required - names)
            self.assertNotIn("mcp.json", names)
            self.assertNotIn(".mcp.json", names)
            self.assertNotIn(".app.json", names)
            self.assertFalse(any(name.startswith(".agents/") for name in names))


if __name__ == "__main__":
    unittest.main()
