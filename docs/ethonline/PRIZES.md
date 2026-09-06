# ETHOnline 2026 partner qualification status

Reviewed 6 September against the [official prize page](https://ethglobal.com/events/ethonline2026/prizes).
Earlier pool amounts and completed-integration claims in this document were superseded
by the implementation audit. Dashboard selections have not been verified.

| Partner | Intended track | Evidence still required |
|---|---|---|
| The Graph | Best AI Tooling or AI Use Case with The Graph (Continuity) | Live trace recorded; final video and Dashboard prize selection remain |
| Bazantic | Help an Agent Use Your Hackathon Project (Continuity) | Paired comparison recorded (3/3 both); human review remains, no uplift claim |
| Ledger | Continuity | Device/tool qualification evidence; schema validation and terminal simulation alone do not establish Clear Signing |

The Graph is the live source of event data. Its repaired runtime path and the
fail-closed AI client are implemented. The new model-backed rehearsal is verified
in deployments/live-e2e-2026-09-06.json, including safe no-send reconciliation.
The old deterministic pause receipt is not the evidence used for this claim.

Bazantic artifacts provide read-only MCP tools and a Recipe. Payload hashes provide
integrity checking, not chain/provider authenticity. Payment settlement is not
implemented. Do not claim paid agent access or use the superseded synthetic scores.

Ledger's descriptor passes the official v1 schema. The owner CLI checks the hardware
address before signing. Neither hardware rendering nor a Ledger-signed recovery is
yet evidenced. The previous keyring helper remains an optional integration surface,
not proof that Ledger infrastructure is used by the keeper at runtime.

Submit only accurate descriptions from SUBMISSION_PACK.md. Applying for a prize
is not a statement that the organizers have confirmed eligibility.

Owner confirmed no Ledger device on 6 September. Current submission preparation
therefore retains Ledger as a schema/CLI prototype and excludes a hardware Clear
Signing qualification claim. Revisit a Ledger prize only with new device evidence.
