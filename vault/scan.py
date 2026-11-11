#!/usr/bin/env python3
"""Harvest API keys from configured harvest documents."""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_DIRS = [
    "~/Loosies",
    "~/Notes",
    "/storage/ED7B-AD5A/r26/Loosies",
    "/storage/ED7B-AD5A/r26/Notes",
    "/storage/ED7B-AD5A/root_2026/Sorties",
    "/storage/emulated/0/RECOVERY_ZONE/Loosies",
    "/storage/emulated/0/RECOVERY_ZONE/Notes",
]
TEXT_SUFFIXES = {".md", ".markdown", ".txt"}

PROVIDERS = [
    ("openrouter", [re.compile(r"sk-or-v1-[A-Za-z0-9]{40,}")]),
    ("anthropic", [re.compile(r"sk-ant-[A-Za-z0-9_-]{40,}")]),
    ("openai", [
        re.compile(r"sk-proj-[A-Za-z0-9_-]{40,}"),
        re.compile(r"sk-[A-Za-z0-9]{40,}"),
    ]),
    ("google", [re.compile(r"AIza[0-9A-Za-z_-]{35}")]),
    ("github", [
        re.compile(r"ghp_[A-Za-z0-9]{36}"),
        re.compile(r"gho_[A-Za-z0-9]{36}"),
        re.compile(r"github_pat_[A-Za-z0-9_]{82}"),
    ]),
    ("groq", [re.compile(r"gsk_[A-Za-z0-9]{40,}")]),
    ("huggingface", [re.compile(r"hf_[A-Za-z0-9]{30,}")]),
    ("nvidia", [re.compile(r"nvapi-[A-Za-z0-9_-]{40,}")]),
    ("perplexity", [re.compile(r"pplx-[A-Za-z0-9]{40,}")]),
    ("cerebras", [re.compile(r"csk-[A-Za-z0-9]{40,}")]),
    ("fireworks", [re.compile(r"fw_[A-Za-z0-9]{40,}")]),
]

try:
    from . import test_keys
except ImportError:  # pragma: no cover - direct script execution
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import test_keys

_ORIGINAL_TEST_KEY = test_keys.test_key
test_key = test_keys.test_key


def _verify_key(provider, token):
    """Use a patched scan-level tester when one is present."""
    current = globals().get("test_key")
    if callable(current) and current is not _ORIGINAL_TEST_KEY:
        return current(provider, token)
    return test_keys.test_key(provider, token)


def harvest_dirs():
    """Return configured harvest directories, preserving order."""
    extra = os.environ.get("HARVEST_DIRS", "")
    if extra.strip():
        dirs = [part for part in extra.split(":") if part.strip()]
    else:
        dirs = [os.path.expanduser(path) for path in DEFAULT_DIRS]
    seen = set()
    result = []
    for path in dirs:
        expanded = os.path.expandvars(os.path.expanduser(path))
        if expanded not in seen:
            seen.add(expanded)
            result.append(expanded)
    return result


def candidate_files(root):
    """Yield text files under root without following links."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for filename in filenames:
            if Path(filename).suffix.lower() in TEXT_SUFFIXES:
                yield Path(dirpath) / filename


def redact(token):
    if len(token) <= 12:
        return "***"
    return token[:8] + "..." + token[-4:]


def scan():
    found = {}
    source_count = 0
    file_count = 0
    for root in harvest_dirs():
        if not os.path.isdir(root):
            continue
        for path in candidate_files(root):
            file_count += 1
            try:
                with path.open("r", encoding="utf-8", errors="ignore") as handle:
                    for line_number, line in enumerate(handle, 1):
                        for provider, patterns in PROVIDERS:
                            for pattern in patterns:
                                for match in pattern.finditer(line):
                                    token = match.group(0)
                                    source = {
                                        "path": str(path),
                                        "line": line_number,
                                    }
                                    key = hashlib.sha256(
                                        token.encode("utf-8")
                                    ).hexdigest()
                                    if key not in found:
                                        found[key] = {
                                            "provider": provider,
                                            "token": token,
                                            "sources": [],
                                        }
                                    sources = found[key]["sources"]
                                    if source not in sources:
                                        sources.append(source)
                                    source_count += 1
            except OSError:
                continue

    report_rows = []
    vault_keys = []
    for item in found.values():
        result = _verify_key(item["provider"], item["token"])
        if hasattr(result, "status") and hasattr(result, "code"):
            status, code = result.status, result.code
        elif isinstance(result, (tuple, list)):
            status = result[0]
            code = result[1] if len(result) > 1 else None
        elif isinstance(result, dict):
            status = result.get("status")
            code = result.get("code")
        elif hasattr(result, "status"):
            status = result.status
            code = getattr(result, "code", None)
        else:
            status = str(result)
            code = None
        sources = item["sources"]
        report_rows.append((status, item["provider"], item["token"], sources, code))
        if status == "WORKING":
            vault_keys.append({
                "name": item["provider"],
                "provider": item["provider"],
                "token": item["token"],
                "sources": sources,
            })

    vault_path = Path("vault.v3.json")
    with vault_path.open("w", encoding="utf-8") as handle:
        json.dump({"version": 3, "keys": vault_keys}, handle, indent=2)
        handle.write("\n")

    report_path = Path("harvest_report.txt")
    with report_path.open("w", encoding="utf-8") as handle:
        for status, provider, token, sources, code in report_rows:
            report_status = "OK" if status == "WORKING" else status
            source_text = ", ".join(
                f"{source['path']}:{source['line']}" for source in sources
            )
            code_text = "" if code is None else f" ({code})"
            handle.write(
                f"{report_status} {provider} {redact(token)} "
                f"{source_text}{code_text}\n"
            )

    working_count = sum(
        1 for row in report_rows if row[0] == "WORKING"
    )
    print(
        f"scanned {file_count} files, found {len(found)} unique keys, "
        f"{working_count} working"
    )
    print(f"wrote {vault_path} and {report_path}")
    return 0


def main():
    return scan()


if __name__ == "__main__":
    sys.exit(main())
