# CWF401 — live review rehearsal

Date: 1 October 2026. Implementation: `feat/colosseum-review`, through `4144eeb`.
Scope: public Base Sepolia/Graph reads and local review records.

## Measured machine evidence

- The observer verified five historical withdrawals against chain 84532, the
  supported vault, canonical blocks, receipt status and exact emitted fields.
- Policy `single-withdrawal-v1` uses strict integer `amount > 10000000000000000000`.
  Four withdrawals of 25000000000000000000 opened four cases; the 100-unit
  event produced no case. These are valueless DemoVault accounting units.
- Repeat observation added zero rows. Reopening the store and draining pending
  evaluations returned zero new evaluations; all five observations/four cases survived.
- Live `serve` on 127.0.0.1:8089 resumed the same store and showed five observations,
  four cases and healthy source checks. Guardian paused=true is a separate RPC
  snapshot read. A case is not evidence that this new feature paused the Guardian.
- No keeper/model was configured; no new chain transaction was sent.
- Actual source records: observer-live-2026-10-01.json and review-live-2026-10-01.json.
  Historical event dates must remain visible in any recording.

## Exact negative event in the 2 October capture

The read-only capture in `.sentinel/cwf404-live.sqlite3` contains an evaluation
for every one of the five historical observations. The event without a case is:

- Source ID: `0xdbcd8310df34fcf5750f47948346791b0a0fe54ab2c08ed2e4a4e6efa20aabedca000000`.
- Transaction: `0xdbcd8310df34fcf5750f47948346791b0a0fe54ab2c08ed2e4a4e6efa20aabed`;
  block **46428477**, log index **202**.
- Amount **100**, threshold **10000000000000000000**, comparison strictly `>`.
  Recorded `breached=false`, `case_id=null`, reason:
  `Withdrawal is within configured limit`.

This is 100 literal valueless accounting units, with no decimal/unit conversion.
It was evaluated and retained; it was not dropped. All four remaining events are
25000000000000000000 and have deterministic case IDs. The full five-row mapping
is in `cwf405-evidence.json`; it was extracted using SQLite read-only mode, without
changing the original human-session database or issuing another chain transaction.

## First human session

The owner selected themselves as the first operator. The live case
`bbbfdd578c1c38f2ce01726e57bd6d92943b651977ccd3614f1d256f642ccaf9`
was acknowledged at **2026-10-01T18:32:58.037924Z**, revision 1.
The owner reported the matching Review history; the live UI confirmed it.
The locally declared operator label and note were both `1222`. They establish
use of the acknowledgment control, not a substantive incident assessment.

Resolution, downloaded brief, elapsed time and qualitative feedback are pending.
Do not substitute the automated fixture session for those missing observations.
Legacy action evidence is not connected in this live session; the UI reports
`not_configured` and the corresponding gap.

Read-only machine capture: `first-operator-live-2026-10-01.json` and
`first-operator-brief.{json,txt}`. Actual human-session screen:
`ui-first-operator-acknowledged.jpg`. The agent's captured brief is not evidence
that the human downloaded it.

## Reproduction

1. Run the live command in RUNBOOK.md against the same review file.
2. Check source freshness; open the case and compare amount, threshold, source ID
   and original verification evidence. Read the legacy-evidence gap.
3. The human enters their own label/note and acknowledges an open case.
4. The human enters a reasoned note and chooses their own disposition, then resolves.
5. Export JSON/text briefs; compare the displayed revision/history with the files.
6. After the session, stop/restart the service and verify the same case and history.
   Avoid restarting while the operator is typing. Record the actual counts/revisions.

A future controlled withdrawal rehearsal requires separate operational
authorization and real transaction/receipt evidence. Existing historical
observations already support the first read-only spike; they are not a new withdrawal.
