# ETHOnline 2026 — partner strategy

> Verified on 3 September 2026 against
> <https://ethglobal.com/events/ethonline2026/prizes>.

## Decision

The only partner priority is **Best AI Tooling or AI Use Case with The Graph
(Continuity)**, a $5,000 pool with a $2,500 / $1,500 / $1,000 award breakdown.
Actual selection remains pending in the submission form.

Do not add another sponsor until the complete flow works:

```text
live Graph event → Graph-derived AI classification → deterministic policy
→ durable reservation → pause → confirmations → state verification
```

## Qualification map

| Requirement | Sentinel implementation | Required evidence |
|---|---|---|
| The Graph is load-bearing | Runtime reads live Vault entities from a Graph provider | Subgraph ID/version, query, live trace |
| Live provider data | Studio/API-key or Graph Market endpoint | Indexed block and real transaction/entity |
| Meaningful AI use | Graph-derived features enter structured classification | Input/features, schema-valid output, decision trace |
| Reasoning/automation | Classification affects incident decision; deterministic policy controls permission | End-to-end run plus negative path |
| Continuity lineage | Existing project is extended | Full history, baseline tag, prior/new table |
| Open source and runnable | Public repository with clear README | Anonymous clean-clone test |
| Demo | Working integration in 2–4 minutes | Public video URL |

If the demo shows only a deterministic threshold and AI output does not affect
reasoning, decision, or automation, the AI qualification has not been proven.
Invalid, adversarial, timed-out, or low-confidence model output must fail closed.

## Tracks not selected

- Do not apply to The Graph composable/standardized track for one standalone
  Subgraph; that track requires composition or meaningful standardized-schema use.
- 0G is not listed as an ETHOnline 2026 partner and is out of scope.
- Do not use deprecated Chainlink Automation as a fallback; current Chainlink
  guidance points such workflows to CRE.
- Leave partner slots two and three empty unless a complete, load-bearing
  integration already exists before feature freeze.

## Gate

Keep The Graph as the target only after a live provider query returns a real Base
Sepolia event and the measured latency supports either Graph-first or an honestly
documented hybrid architecture.
