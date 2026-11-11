# TASK

Build a key-harvesting and credential-injection system for a Termux/Android
development environment. Output is a working CLI toolchain, not a plan. The
repo you are writing into is empty; you populate it.

# ENVIRONMENT (verified, do not re-derive)

- OS: Termux on Samsung Android tablet, no root, no proot, no container.
- Termux home: /data/data/com.termux/files/home
- Shared storage (FUSE, slow but readable): /storage/emulated/0
- SD card: /storage/ED7B-AD5A
- Available: python3, node, npm, git, curl, jq, rg, sqlite3, clang, rustc,
  cargo, go, termux-api, termux-keystore
- Missing: gpg, age, pass, sops
- /tmp NOT writable - use $HOME/.cache/
- ~/.local/bin on PATH (duplicated, harmless)

# WHAT THE USER ACTUALLY WANTS

User has spent 18 months building an AI agent ecosystem across 3 devices.
The Chromebook they developed on is physically broken. Development is
Android-only now. They want, in order:

1. HARVEST. Scan human-authored harvest docs (markdown/txt files where the
   user manually pasted API keys over hours of work). Extract keys. Test
   against real provider endpoints. Write one unified vault.
2. VAULT. Single source of truth. Flat JSON. One file. No .env, no scattered
   configs, no canonical-vs-legacy duplication.
3. VALET. Wrapper script that reads the vault, exports keys as env vars, and
   execs the child. Key gone from process table when child dies. Never touches
   disk. Never touches git.
4. FALLBACK. On rate-limit signal (429 in stderr, or child exit code 2), re-exec
   with next provider in configured chain.
5. (SECONDARY, do not start here) Help untangle 6+ project generations across
   5 storage roots. Wait until 1-4 are shipped and verified.

# SOURCE OF TRUTH HIERARCHY

1. Harvest docs (user hand-authored, HIGHEST). Scan dirs:
   - ~/Loosies
   - ~/Notes
   - /storage/ED7B-AD5A/r26/Loosies
   - /storage/ED7B-AD5A/r26/Notes
   - /storage/ED7B-AD5A/root_2026/Sorties
   - /storage/emulated/0/RECOVERY_ZONE/Loosies
   - /storage/emulated/0/RECOVERY_ZONE/Notes
   Accept additional dirs via HARVEST_DIRS env var (colon-separated).
2. The vault the harvester writes.
3. Nothing else. Any existing vault.json, config file, or session log that
   contains key-shaped strings is a DOWNSTREAM CACHE - may be stale, may
   contain fabricated keys from agent sessions.

# KNOWN-BROKEN (do not rebuild, do not re-diagnose)

See KNOWN-BROKEN.md. Summary: opencode 1.17.8 crashes with a Rust panic.
gemini-cli works via OAuth (not vault keys). 9router entry points at a local
router that no longer exists. gemini and mistral keys in vault.json.v2 are
dead. kilo key is a 12-char placeholder.

# WHAT TO BUILD

- README.md (already exists, do not rewrite)
- SPEC.md (this file)
- KNOWN-BROKEN.md (already exists)
- FAILURE-MODES.md (already exists - read before writing code)
- bin/valet (already exists and works - only extend if adding features)
- vault/scan.py (STUB - implement)
- vault/test_keys.py (STUB - implement)
- bin/valet-rotate (write this)
- tests/ (write these)

## scan.py

1. Walk HARVEST_DIRS.
2. Regex-match keys by provider prefix:
   - openrouter:  sk-or-v1-[A-Za-z0-9]{40,}
   - anthropic:   sk-ant-[A-Za-z0-9_-]{40,}
   - openai:      sk-proj-[A-Za-z0-9_-]{40,}  OR  sk-[A-Za-z0-9]{40,}
   - google:      AIza[0-9A-Za-z_-]{35}
   - github:      ghp_[A-Za-z0-9]{36} OR gho_[A-Za-z0-9]{36}
                  OR github_pat_[A-Za-z0-9_]{82}
   - groq:        gsk_[A-Za-z0-9]{40,}
   - huggingface: hf_[A-Za-z0-9]{30,}
   - nvidia:      nvapi-[A-Za-z0-9_-]{40,}
   - perplexity:  pplx-[A-Za-z0-9]{40,}
   - cerebras:    csk-[A-Za-z0-9]{40,}
   - fireworks:   fw_[A-Za-z0-9]{40,}
3. For each match: token, provider, source path, line number.
4. Dedupe by sha256 of token.
5. Call test_keys.py to verify. Only WORKING keys go in vault.
6. Write vault.v3.json (schema below).
7. Full report to harvest_report.txt (OK/DEAD/UNVERIFIED per key).

vault.v3.json schema:
{
  "version": 3,
  "keys": [
    {
      "name": "openrouter",
      "provider": "openrouter",
      "token": "...",
      "sources": [{"path": "...", "line": 42}]
    }
  ]
}

## test_keys.py

Real HTTP request per key, 8s timeout:

- openrouter:  GET https://openrouter.ai/api/v1/auth/key, Bearer
- anthropic:   GET https://api.anthropic.com/v1/models, x-api-key + version
- openai:      GET https://api.openai.com/v1/models, Bearer
- google:      GET https://generativelanguage.googleapis.com/v1beta/models?key=<key>
- github:      GET https://api.github.com/user, token header
- groq:        GET https://api.groq.com/openai/v1/models, Bearer
- huggingface: GET https://huggingface.co/api/whoami-v2, Bearer
- nvidia:      GET https://integrate.api.nvidia.com/v1/models, Bearer
- perplexity:  GET https://api.perplexity.ai/models, Bearer

200 = WORKING, other = DEAD with code, exception = UNVERIFIED.
Vault gets WORKING only. Report gets all three.

## bin/valet-rotate

Usage: valet-rotate <provider1,provider2,...> <command...>
Exports first provider key, execs command. On child exit code 2 (aider
rate-limit) or 429 in last 50 lines of stderr, tries next provider.
Final failure prints which providers were tried.

# HARD CONSTRAINTS

1. Ask before running reconnaissance. Do not scan whole filesystem.
   Do not look at ~/.codex/sessions/* or ~/.gemini/tmp/* without permission.
2. No shell heredocs in instructions to the user. They are on Android,
   terminal is small, heredocs scroll off screen. Write files via git commit.
3. No .env. No dotenv. No put-your-key-in-a-config-file. One vault, one format.
4. No single-line strings longer than 120 chars in generated code. Break lines.
5. Termux paths not Linux desktop paths. $HOME not ~/. /data/data/com.termux/...
   when absolute is needed. No /tmp.
6. Runnable with stdlib Python + jq + curl. No pip installs, no node, no rust,
   no go in the valet path.
7. valet must work offline. Vault is local. Only fails if child fails.

# ACCEPTANCE TESTS (must pass before claiming done)

1. `python3 vault/scan.py` on a fixture harvest doc finds N keys with correct
   provider classification and source attribution.
2. `python3 vault/test_keys.py` on a known-bad key returns DEAD with HTTP code.
3. `bin/valet bash -c env` prints expected key vars from a fixture vault.
   Deleting the vault causes non-zero exit with vault-missing message.
4. `bin/valet-rotate provider1,provider2 bash -c exit_2` tries next provider.
   Test with mock child.
5. (User verifies) `bin/valet aider --model openrouter/... ~/RootBase_Unified`
   gets a real coding session.

Every claim in your final report must cite actual command output. Saying
I tested it works with no output means you did not test it.

# FORBIDDEN BEHAVIORS

Read FAILURE-MODES.md. Short: no fabrication, no drift, no silent failures.
Every claim backed by pasted output.

# DELIVERABLE

- The repo with all files above, tested, README explaining user workflow in
  5 steps or fewer.
- CHANGELOG.md: what you built, what you verified (with output), what you did
  NOT verify and why, what you left for later.
- NO additional architecture. NO while-I-was-in-there refactors.

Start by reading this file, KNOWN-BROKEN.md, and FAILURE-MODES.md. Ask the
user two questions max before building. Then build the 2 stub files and the
1 wrapper. Run acceptance tests 1-4. Report with pasted output.
