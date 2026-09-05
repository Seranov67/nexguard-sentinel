# Local recovery snapshots

`NexGuard-Sentinel-prestart-2026-09-03-rules.zip` is the earlier snapshot after
the rule/compliance documentation pass. Its SHA-256 is stored beside it, and a
45-file restore/hash comparison passed on 3 September 2026.

`NexGuard-Sentinel-prestart-2026-09-04-english-clean.zip` is the current clean
English-language snapshot. It excludes root and nested caches, generated
dependencies, compiler binaries, `.env`, and other secret-bearing state. Its
SHA-256 is stored beside it, and a 45-file restore/hash comparison passed.

`NexGuard-Sentinel-prestart-2026-09-04-english.zip` is superseded because it
accidentally included ignored root `.mypy_cache` and `.ruff_cache` directories.
Do not use it as the clean recovery artifact.

`NexGuard-Sentinel-prestart-2026-09-03.zip` is the earlier Phase 0 snapshot and is
retained as historical recovery evidence. Neither archive is an off-device backup.

The archives exclude `.env`, `.venv`, `.solcx`, `node_modules`, caches and the
`backups` directory itself.
