# Known-broken on this device

Termux on Samsung A9, no root, no proot. Verified. Do not re-diagnose.

## opencode 1.17.8

Crashes with Rust panic in `simd_path.rs` - `index out of bounds: len is 32,`
`index is 32`. Off-by-one UTF-8 width bug in their renderer. Not fixable
client-side. Do not suggest it.

## gemini-cli

Works. Uses OAuth, not vault keys. User has used it 1.5+ years. Do not
suggest it as a discovery. Do not point it at a vault key.

## 9router

`vault.json.v2` has a `9router` entry pointing at `http://localhost:20128/v1`.
That was a local router on the Chromebook, which is physically broken
(screen destroyed). No 9router process exists on this device. Do not point
any tool at it.

## gemini key in vault.json.v2

56 chars, `AIza` prefix. Returns HTTP 400 `API key not valid`. Dead.

## mistral key in vault.json.v2

46 chars. Returns HTTP 401. Dead.

## kilo_api_key in vault.json.v2

12 chars. Placeholder, never a real credential. Ignore.

## /tmp

Not writable. Use `$HOME/.cache/` instead.

## ~/.local/bin on PATH

Duplicated (appears twice). Cosmetic. Ignore.
