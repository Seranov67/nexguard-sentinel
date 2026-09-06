# Prior-work disclosure

This document separates work that existed before ETHOnline 2026 from work that
is being produced during the event. The intended submission pool is The Graph
AI/Continuity; actual Dashboard selection remains pending. Only event-period
feature work will be presented for judging.

Publication repository: <https://github.com/Seranov67/nexguard-sentinel>.
The owner selected this new repository on 5 September 2026 for clearer naming.
The complete original Git history and pre-event baseline are preserved; a new
repository name does not make the pre-existing work event-period work.

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
The ETHOnline feature is currently a separate onchain module alongside the IoT
controller. It adapts resilience concepts; no integration with the old controller
or reuse of its runtime code is claimed at this stage. Any later reuse will be
identified explicitly rather than represented as new event work.

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

The repository preserves the pre-event history. The annotated tag
`pre-ethonline-2026` resolves to the baseline above. The event branch was created
after the confirmed 4 September 19:00 Kyiv start. Contracts, live Graph ingestion, durable state, the fail-closed AI transport and
verified executor are implemented and locally tested as of 6 September. The final
real-model end-to-end demonstration remains pending.
See `COMPLIANCE.md` and `deployments/` for verified evidence.

## 6. Support communication

No support ticket is claimed as filed in this document. If a ticket is sent,
its date, channel and response will be recorded here after the fact.

**Ticket status:** no sent support disclosure or organizer response verified as
of 5 September 2026. Prepared wording is in `../../submission/FORM-DRAFT.md`.

## 7. Evidence limitations

- The statement that the DoraHacks BUIDL was never published is based on the
  repository's still-pending submission placeholder and owner representation; no
  public submission URL is known. Verify once more before final submission.
- Exact raw prompts from earlier Claude sessions are not present locally; see
  `AI_PROMPTS.md` and do not reconstruct them as verbatim history.
- The new contract and Graph evidence is recorded in `deployments/`; this does
  not independently prove a real-model run of the repaired automated protection.
