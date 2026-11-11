import contextlib
import io
import socket
import subprocess
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import vault.test_keys as test_keys


class TestKeysTests(unittest.TestCase):
    def test_known_bad_key_returns_dead(self):
        error = urllib.error.HTTPError(
            "https://api.openai.com/v1/models",
            401,
            "Unauthorized",
            {},
            None,
        )
        with patch(
            "vault.test_keys.urllib.request.urlopen",
            side_effect=error,
        ):
            result = test_keys.test_key("openai", "sk-" + ("a" * 40))
        self.assertEqual(result.status, "DEAD")
        self.assertEqual(result.code, 401)
        self.assertEqual(result[0], "DEAD")
        self.assertEqual(result["status"], "DEAD")

    def test_timeout_returns_unverified(self):
        seen = {}

        def fake_urlopen(request, timeout=None):
            seen["timeout"] = timeout
            raise socket.timeout("timed out")

        with patch(
            "vault.test_keys.urllib.request.urlopen",
            side_effect=fake_urlopen,
        ):
            result = test_keys.test_key(
                "openai", "sk-" + ("a" * 40), timeout=0.01
            )
        self.assertEqual(result.status, "UNVERIFIED")
        self.assertIsNone(result.code)
        self.assertEqual(seen["timeout"], 0.01)

    def test_cli_reports_dead_key(self):
        error = urllib.error.HTTPError(
            "https://api.openai.com/v1/models",
            401,
            "Unauthorized",
            {},
            None,
        )
        with patch(
            "vault.test_keys.urllib.request.urlopen",
            side_effect=error,
        ):
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = test_keys.main(["openai", "sk-" + ("a" * 40)])
        self.assertNotEqual(code, 0)
        self.assertIn("DEAD", stdout.getvalue())
        self.assertIn("401", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
