# Bazantic real-model A/B: 6 September 2026

A real local Qwen3 4B run used the same persisted live incident, task, read-only
tools, temperature 0, 512-token response budget and 120-second request timeout.
Only Recipe guidance differed. This is one paired run, not a statistical evaluation.

| Condition | Transaction hash | Explorer link | Integrity tool | Total |
|---|---|---|---|---|
| Without Recipe | PASS | PASS | PASS | 3/3 |
| With Recipe | PASS | PASS | PASS | 3/3 |

**No structural improvement was demonstrated.** Both conditions called
get_latest_incident and verify_incident_evidence; the tool returned verified=true
for payload integrity only. Neither condition proves payment settlement or gateway
registration. Local Evidence API demo mode was explicitly enabled.

## Accuracy review: AI-assisted findings, human review pending

- Without Recipe, the model rewrote the 10^19 accounting-unit threshold as 10^18.
  Its response ends with an unfinished list item under the bounded output budget.
- With Recipe, the model incorrectly described 25e18 as "25 million units" and
  called velocity_bps "basis points per second" without evidence for that unit.
- The structured feature record has one new withdrawal; language suggesting a
  sustained burst or real-value custody overstates the evidence.
- With Recipe, the response correctly states the boundary between payload
  integrity and independent chain verification.

These outputs must not be presented as accurate causal explanations or a measured
Recipe uplift. Preserve the numeric feature trace as the source of truth. Human
review remains required before submitting any explanation-quality claim.

[Unedited responses and tool transcripts](deployments/bazantic-ab-2026-09-06.json)
include the actual incident and verified pause hash. The previous simulated 1/4
versus 4/4 report is superseded and remains only in Git history.

## Reproduce

```bash
# Reachable local model; Evidence API uses the persisted incident and demo opt-in.
EVIDENCE_API_URL=http://127.0.0.1:8088 python -m sentinel.bazantic.benchmark_ab \
  --model qwen3:4b-instruct-2507-q4_K_M --timeout 120 --output benchmark.md
```

The initial fixed-30-second CPU attempt timed out and produced no fabricated score.
The explicit benchmark timeout is bounded at 120 seconds and does not change the
Sentinel action classifier's fail-closed timeout.
