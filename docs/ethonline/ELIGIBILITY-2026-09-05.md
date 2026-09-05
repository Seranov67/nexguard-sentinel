# Eligibility review — 5 September 2026

This is a source-based readiness review, not organizer approval or a guarantee.

Sources checked: https://ethglobal.com/rules,
https://ethglobal.com/events/ethonline2026/info/start,
https://ethglobal.com/events/ethonline2026/info/details,
https://ethglobal.com/events/ethonline2026/prizes/the-graph.

## Evidence supported

- Participant screenshots show confirmed attendance and Continuity selected in
  the project prize form. The new repository is public and preserves the complete
  original history plus `pre-ethonline-2026` at the disclosed baseline.
- No rule requiring equal project/repository names was found. Changing repository
  name does not remove the obligation to disclose prior code and planning.
- The public README distinguishes the old IoT MVP, the new Sentinel module and
  unfinished functionality. Graph Studio deployment and a live entity are evidenced.

## Still required before claiming qualification

- Select The Graph in the submission form when enabled and verify saving. The
  screenshots show disabled form sections; selection is NOT yet completed.
- Send written prior-work disclosure to ETHGlobal and retain delivery evidence.
  A local/public disclosure file is not evidence of direct organizer notification.
- Complete meaningful Graph-driven AI behavior and an end-to-end demonstration.
  Live query output alone is insufficient for the AI prize.
- Include accurate AI attribution, human decisions/testing, specifications and
  available prompts. Earlier Claude prompt history is missing and remains an
  explicit evidence gap. Never share raw conversation exports containing keys.
- Record a human-narrated 2–4 minute video at 720p or higher, without speed-up,
  mobile capture or synthetic voice; add working demo/repository links.
- Verify final form completion and submit before 13 September 19:00 Kyiv.
- GitHub Actions success is not verified: the public runs endpoint currently
  returns no runs. Local tests are not described as hosted CI success.

## Prepared organizer notice — not sent

We selected Continuity for ETHOnline 2026. NexGuard Sentinel is published at
https://github.com/Seranov67/nexguard-sentinel with the full history of our existing
MIT-licensed nexguard-edge-resilience IoT project. The pre-event baseline is
fa202e994a77ea365061f6ac609daea1b5ad60dd, tagged pre-ethonline-2026. Pre-event
planning/spikes and design references (latch-agent and LLM-Log-Monitor) are disclosed
in docs/ethonline/DISCLOSURE.md. New event work includes Base Sepolia contracts,
a live Subgraph and Python SQLite state; the automated loop and AI are still in
development. Please let us know if you require any additional Continuity disclosure.

## Verdict

Development verification: the ES302 ingestion component passes six new tests;
the full Python suite passes 80 tests. Ruff, strict Sentinel MyPy, Compose and
history secret scans pass. Live transport integration remains incomplete:
Python urllib received HTTP 403; Node fetched a historical Graph snapshot but
its `_meta.block.hash` was null. The current strict validator rejects this
snapshot. Resolve optional metadata semantics with canonical chain verification
before enabling execution; do not report the new ingestion runtime as live-ready.

No verified naming/history issue was found that by itself establishes
disqualification. Final eligibility is not yet established. Concealing prior work,
misrepresenting AI/human contribution, missing partner selection or incomplete
submission can affect eligibility. The organizers make the final determination.
