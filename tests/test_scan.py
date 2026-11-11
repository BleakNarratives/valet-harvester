import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import vault.scan as scan


class ScanTests(unittest.TestCase):
    def setUp(self):
        cache = Path.home() / ".cache" / "valet-tests"
        cache.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=str(cache))
        self.root = Path(self.tmp.name)
        self.old_cwd = os.getcwd()
        self.old_env = os.environ.get("HARVEST_DIRS")
        os.chdir(self.root)
        harvest = self.root / "harvest"
        harvest.mkdir()
        token = "sk-or-v1-" + ("a" * 40)
        (harvest / "notes.md").write_text(
            f"pasted key: {token}\n", encoding="utf-8"
        )
        os.environ["HARVEST_DIRS"] = str(harvest)

    def tearDown(self):
        os.chdir(self.old_cwd)
        if self.old_env is None:
            os.environ.pop("HARVEST_DIRS", None)
        else:
            os.environ["HARVEST_DIRS"] = self.old_env
        self.tmp.cleanup()

    @patch("vault.scan.test_key", return_value=("WORKING", 200))
    def test_finds_working_key(self, _mock):
        result = scan.main()
        self.assertEqual(result, 0)
        vault = json.loads((self.root / "vault.v3.json").read_text())
        self.assertEqual(vault["version"], 3)
        self.assertEqual(len(vault["keys"]), 1)
        key = vault["keys"][0]
        self.assertEqual(key["provider"], "openrouter")
        self.assertTrue(key["token"].startswith("sk-or-v1-"))
        self.assertEqual(key["sources"][0]["line"], 1)
        self.assertIn("notes.md", key["sources"][0]["path"])
        report = (self.root / "harvest_report.txt").read_text()
        self.assertIn("OK openrouter", report)

    @patch("vault.scan.test_key", return_value=("DEAD", 401))
    def test_dead_key_is_excluded(self, _mock):
        result = scan.main()
        self.assertEqual(result, 0)
        vault = json.loads((self.root / "vault.v3.json").read_text())
        self.assertEqual(vault["keys"], [])
        report = (self.root / "harvest_report.txt").read_text()
        self.assertIn("DEAD openrouter", report)
        self.assertIn("401", report)

    @patch("vault.scan.test_key", return_value=("WORKING", 200))
    def test_same_key_collects_sources(self, _mock):
        harvest = Path(os.environ["HARVEST_DIRS"])
        token = "sk-or-v1-" + ("b" * 40)
        (harvest / "second.md").write_text(
            f"again: {token}\n", encoding="utf-8"
        )
        (harvest / "notes.md").write_text(
            f"first: {token}\n", encoding="utf-8"
        )
        result = scan.main()
        self.assertEqual(result, 0)
        vault = json.loads((self.root / "vault.v3.json").read_text())
        self.assertEqual(len(vault["keys"]), 1)
        self.assertEqual(len(vault["keys"][0]["sources"]), 2)


if __name__ == "__main__":
    unittest.main()
