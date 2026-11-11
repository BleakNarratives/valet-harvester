# CHANGELOG

## Built

- Security hardening: generated vault/report files use mode 0600,
  symlinked harvest files are ignored, and generated secret files are
  gitignored.
-  `vault/scan.py`: recursive harvest scanning, provider regexes, SHA-256 deduplication, verification, `vault.v3.json`,
and `harvest_report.txt`.
- `vault/test_keys.py`: real endpoint checks with an 8-second timeout.
- `bin/valet-rotate`: provider fallback on exit code 2 or stderr 429.
- `tests/`: scan, key testing, and rotation tests.

## Verified

- `python3 -m unittest discover -s tests -p 'test_*.py'`:
  `Ran 10 tests in 1.230s` / `OK`
- Acceptance 1: `scanned 2 files, found 1 unique keys, 0 working`
- Acceptance 2: `DEAD 401` with exit code 1
-  Acceptance 3: printed `GEMINI_API_KEY`, `GOOGLE_GENERATIVE_AI_API_KEY`, and `MISTRAL_API_KEY`; missing vault exited 1
with `vault missing: ...`
- Acceptance 4: printed `worked with token2` with exit code 0

## Not verified

- Live provider keys and acceptance test 5 require the user's real credentials and device.

## Left for later

- Untangling the older project generations across storage roots.
