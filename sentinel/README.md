# Sentinel durable core (ES301)

Requires Python 3.12. The ES301 runtime uses only the standard library and adds
no third-party runtime dependencies. `Settings.from_env` accepts the public
runtime fields from `.env.ethonline`; loading that file is the caller's job.
The pre-event YAML file remains an architectural template, not an executable
runtime configuration. No signer, AI client or executor is implemented here.

SQLite uses WAL, FULL synchronous writes, foreign keys and immediate write
transactions. Event/cursor updates and reservation/source-event ownership are
atomic. Unfinished intents block additional reservations after restart. Conflicting
event replays and storage errors raise and must stop processing. Sequence values
are decimal strings in storage to avoid SQLite's signed 64-bit limit.

`reserve` enforces storage exclusivity only; ES302 must perform cooldown, budget,
chain, contract and action policy checks in the same reservation transaction.
`finish` records evidence supplied by the future verifier; it does not establish
onchain success itself. Latch reset and notification delivery are not implemented.
An indeterminate latch remains set even when a later reconciliation resolves an
intent, until an attributed operator reset is implemented.

Run: `python -m pytest sentinel/tests` and `python -m mypy sentinel --exclude tests`.
