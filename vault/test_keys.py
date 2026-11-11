#!/usr/bin/env python3
"""Test provider API keys against their real endpoints."""

import argparse
import socket
import sys
import urllib.error
import urllib.request
from collections import namedtuple

TIMEOUT_SECONDS = 8

class KeyResult(tuple):
    """Two-value result with optional detail and dict-style access."""

    def __new__(cls, status, code, detail=""):
        obj = super().__new__(cls, (status, code))
        obj.detail = detail
        return obj

    @property
    def status(self):
        return self[0]

    @property
    def code(self):
        return self[1]

    def __iter__(self):
        return iter((self.status, self.code))

    def __len__(self):
        return 2

    def __getitem__(self, key):
        if isinstance(key, str):
            mapping = {
                "status": self.status,
                "code": self.code,
                "detail": self.detail,
            }
            if key not in mapping:
                raise KeyError(key)
            return mapping[key]
        if key == 0:
            return super().__getitem__(0)
        if key == 1:
            return super().__getitem__(1)
        raise IndexError("KeyResult index out of range")

    def __eq__(self, other):
        if isinstance(other, KeyResult):
            return (
                self.status == other.status
                and self.code == other.code
            )
        if isinstance(other, (tuple, list)):
            return (self.status, self.code) == tuple(other)
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        return ("status", "code", "detail")

    def __repr__(self):
        return (
            f"KeyResult(status={self.status!r}, "
            f"code={self.code!r}, detail={self.detail!r})"
        )


def _result(status, code, detail=""):
    return KeyResult(status, code, detail)


def _request(url, headers):
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.status


def _test_openrouter(token):
    return _request(
        "https://openrouter.ai/api/v1/auth/key",
        {"Authorization": f"Bearer {token}"},
    )


def _test_anthropic(token):
    return _request(
        "https://api.anthropic.com/v1/models",
        {
            "x-api-key": token,
            "anthropic-version": "2023-06-01",
        },
    )


def _test_openai(token):
    return _request(
        "https://api.openai.com/v1/models",
        {"Authorization": f"Bearer {token}"},
    )


def _test_google(token):
    return _request(
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"?key={token}",
        {},
    )


def _test_github(token):
    return _request(
        "https://api.github.com/user",
        {"Authorization": f"token {token}"},
    )


def _test_groq(token):
    return _request(
        "https://api.groq.com/openai/v1/models",
        {"Authorization": f"Bearer {token}"},
    )


def _test_huggingface(token):
    return _request(
        "https://huggingface.co/api/whoami-v2",
        {"Authorization": f"Bearer {token}"},
    )


def _test_nvidia(token):
    return _request(
        "https://integrate.api.nvidia.com/v1/models",
        {"Authorization": f"Bearer {token}"},
    )


def _test_perplexity(token):
    return _request(
        "https://api.perplexity.ai/models",
        {"Authorization": f"Bearer {token}"},
    )


TESTERS = {
    "openrouter": _test_openrouter,
    "anthropic": _test_anthropic,
    "openai": _test_openai,
    "google": _test_google,
    "github": _test_github,
    "groq": _test_groq,
    "huggingface": _test_huggingface,
    "nvidia": _test_nvidia,
    "perplexity": _test_perplexity,
}


def test_key(provider, token, timeout=None):
    """Return WORKING, DEAD, or UNVERIFIED for a provider key."""
    global TIMEOUT_SECONDS
    if timeout is None:
        timeout = TIMEOUT_SECONDS
    previous_timeout = TIMEOUT_SECONDS
    TIMEOUT_SECONDS = timeout
    tester = TESTERS.get(provider)
    if tester is None:
        TIMEOUT_SECONDS = previous_timeout
        return _result("UNVERIFIED", None, f"unknown provider: {provider}")
    try:
        status_code = tester(token)
    except urllib.error.HTTPError as exc:
        TIMEOUT_SECONDS = previous_timeout
        return _result("DEAD", exc.code, str(exc.reason))
    except (
        urllib.error.URLError,
        TimeoutError,
        socket.timeout,
        OSError,
    ) as exc:
        TIMEOUT_SECONDS = previous_timeout
        return _result("UNVERIFIED", None, str(exc))
    TIMEOUT_SECONDS = previous_timeout
    if status_code == 200:
        return _result("WORKING", status_code, "ok")
    return _result("DEAD", status_code, "unexpected status")


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Test one provider API key."
    )
    parser.add_argument("provider", nargs="?")
    parser.add_argument("token", nargs="?")
    parser.add_argument("--provider", dest="provider_option")
    parser.add_argument("--token", dest="token_option")
    parser.add_argument(
        "--timeout",
        type=float,
        default=TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--cerebras",
        dest="cerebras_token",
        help="Ignored compatibility option.",
    )
    args = parser.parse_args(argv)
    provider = args.provider or args.provider_option
    token = args.token or args.token_option
    if not provider or not token:
        parser.error("provider and token are required")
    return provider, token, args.timeout


def main(argv=None):
    provider, token, timeout = _parse_args(argv)
    result = test_key(provider, token, timeout=timeout)
    code_text = "" if result.code is None else str(result.code)
    print(f"{result.status} {code_text}".strip())
    if result.status == "WORKING":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
