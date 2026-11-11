import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class RotateTests(unittest.TestCase):
    def setUp(self):
        cache = Path.home() / ".cache" / "valet-tests"
        cache.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=str(cache))
        self.root = Path(self.tmp.name)
        self.vault = self.root / "vault.json"
        self.child = self.root / "child.py"
        data = {
            "version": 3,
            "keys": [
                {
                    "name": "provider1",
                    "provider": "provider1",
                    "token": "token1",
                    "sources": [],
                },
                {
                    "name": "provider2",
                    "provider": "provider2",
                    "token": "token2",
                    "sources": [],
                },
            ],
        }
        self.vault.write_text(json.dumps(data), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def _env(self, vault_path=None):
        env = os.environ.copy()
        env["VALET_VAULT"] = str(vault_path or self.vault)
        return env

    def _write_child(self, source):
        self.child.write_text(source, encoding="utf-8")

    def test_tries_next_provider_on_exit_code_two(self):
        self._write_child(
            "import os, sys\n"
            "if os.environ.get('API_KEY') == 'token1':\n"
            "    sys.stderr.write('rate limit 429\\n')\n"
            "    raise SystemExit(2)\n"
            "print('worked with', os.environ['API_KEY'])\n"
        )
        proc = subprocess.run(
            [
                str(ROOT / "bin" / "valet-rotate"),
                "provider1,provider2",
                sys.executable,
                str(self.child),
            ],
            capture_output=True,
            text=True,
            env=self._env(),
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("worked with token2", proc.stdout)
        self.assertIn("provider1", proc.stderr)

    def test_tries_next_provider_on_stderr_429(self):
        self._write_child(
            "import os, sys\n"
            "if os.environ.get('API_KEY') == 'token1':\n"
            "    sys.stderr.write('HTTP 429 Too Many Requests\\n')\n"
            "    raise SystemExit(0)\n"
            "print('worked with', os.environ['API_KEY'])\n"
        )
        proc = subprocess.run(
            [
                str(ROOT / "bin" / "valet-rotate"),
                "provider1,provider2",
                sys.executable,
                str(self.child),
            ],
            capture_output=True,
            text=True,
            env=self._env(),
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("worked with token2", proc.stdout)
        self.assertIn("provider1", proc.stderr)

    def test_final_failure_lists_providers(self):
        self._write_child(
            "import os, sys\n"
            "sys.stderr.write('rate limit 429\\n')\n"
            "raise SystemExit(2)\n"
        )
        proc = subprocess.run(
            [
                str(ROOT / "bin" / "valet-rotate"),
                "provider1,provider2",
                sys.executable,
                str(self.child),
            ],
            capture_output=True,
            text=True,
            env=self._env(),
        )
        self.assertEqual(proc.returncode, 0 if False else 1)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("all providers failed", proc.stderr)
        self.assertIn("provider1, provider2", proc.stderr)

    def test_missing_vault_fails(self):
        proc = subprocess.run(
            [
                str(ROOT / "bin" / "valet-rotate"),
                "provider1,provider2",
                sys.executable,
                "-c",
                "raise SystemExit(0)",
            ],
            capture_output=True,
            text=True,
            env=self._env(self.root / "missing.json"),
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("vault missing", proc.stderr)


if __name__ == "__main__":
    unittest.main()
