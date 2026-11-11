# valet-harvester

Harvest API keys from hand-authored notes, store one vault, and inject keys into commands.

1. Set `HARVEST_DIRS` to extra scan directories if needed.
2. Run `python3 vault/scan.py`.
3. Check `vault.v3.json` and `harvest_report.txt`.
4. Run a tool with `bin/valet <provider> <command>`.
5. Rotate providers with `bin/valet-rotate <provider1,provider2,...> <command...>`.
