# Prior-work disclosure

This document separates work that existed before ETHOnline 2026 from work that
will be produced during the event. The intended submission pool is The Graph
AI/Continuity; actual Dashboard selection remains pending. Only event-period
feature work will be presented for judging.

## 1. NexGuard Edge Resilience

Repository: <https://github.com/Seranov67/nexguard-edge-resilience>

- License: MIT
- Public since: 25 July 2026
- Last pre-event commit: `fa202e994a77ea365061f6ac609daea1b5ad60dd`
- Commit timestamp: `2026-07-25T15:37:50+03:00`
- History observed on 3 September: 26 commits; clean `main`, matching `origin/main`
- Domain: reliability and automated recovery for IoT gateways
- Blockchain functionality before ETHOnline: none

The repository was built in July 2026 as an MVP intended for a DoraHacks
hackathon. Its README contains a placeholder DoraHacks submission section, but
the BUIDL was never published and the project was not submitted.

Pre-existing components include health monitoring, an incident state machine,
cooldown and sliding-window recovery guards, a latch, and Telegram notification.
The ETHOnline feature will adapt selected concepts and code with attribution;
it will not represent these components as new event work.

## 2. Latch Agent

Repository: <https://github.com/Seranov67/latch-agent>

- License: MIT
- Built before ETHOnline: 4–6 August 2026
- Last observed commit: `e9de4a4cfc457ed791eacb46bfdd53bba78a417d`
- Commit timestamp: `2026-08-06T13:26:04+03:00`
- History observed on 3 September: 36 commits; clean `main`, matching `origin/main`
- Reused as: a design/reference source, not copied TypeScript production code

Its ActionPolicy and SPEC-002 define durable `checkAndReserve`, `finalise`,
`unfinalised`, `reconcileOnStart`, failure latching, and operator-attributed
reset semantics. The Python implementation created during ETHOnline is a new
implementation informed by those semantics. This influence is disclosed because
it is central to the safety model.

## 3. llm-log-monitor

Repository: <https://github.com/Seranov67/LLM-Log-Monitor>

This is a pre-existing self-hosted log analysis system. It is a reference for
operational prompting and structured LLM output. No code is vendored from it.
Any Sentinel classifier code is new event-period work.

## 4. Preparation artifacts

The planning workspace `NexGuard Sentinel` was created before hacking opened.
It contains specifications, architecture notes, configuration examples, demo
prose and throwaway learning spikes. These artifacts are pre-existing planning
material and are not presented as event-period implementation.

If any preparation document is included in the submission, its pre-event origin
remains stated in Git history/README and in this disclosure.

Pre-event AI-assisted artifacts include the audit, plans, rules/prize research,
specification, threat model, disclosure, demo prose, config templates, write-path
spike changes/tests and The Graph spike tooling. They are preparation evidence,
not event-period product implementation.

## 5. Event-period work

The intended new feature, implemented after hacking opens on 4 September 2026,
is the on-chain Sentinel vertical slice:

- a live The Graph Subgraph and durable event ingestion;
- Graph-derived structured AI incident classification;
- Python blockchain client and crash-safe action reservation/reconciliation;
- pause-only automated guardian with post-action state verification;
- Guardian/Vault contracts and an auditable incident reference;
- tests, CI, deployment artifacts and demo documentation.

The submission repository will preserve the pre-event history and mark the final
verified pre-event commit with `pre-ethonline-2026` after the Dashboard-confirmed
hacking start. Until then, this is planned evidence, not a completed claim.

## 6. Support communication

No support ticket is claimed as filed in this document. If a ticket is sent,
its date, channel and response will be recorded here after the fact.

**Ticket status:** not sent as of 3 September 2026, 21:30 Kyiv.

## 7. Evidence limitations

- The statement that the DoraHacks BUIDL was never published is based on the
  repository's still-pending submission placeholder and owner representation; no
  public submission URL is known. Verify once more before final submission.
- Exact raw prompts from earlier Claude sessions are not present locally; see
  `AI_PROMPTS.md` and do not reconstruct them as verbatim history.
- Deployment, Graph, latency and event-period implementation sections remain
  future work until `COMPLIANCE.md` contains evidence.
