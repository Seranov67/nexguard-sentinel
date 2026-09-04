# Threat model

> Scope: ETHOnline 2026 Base Sepolia prototype. This is not a production security
> assessment and does not authorize custody of real funds.

## Assets and trust boundaries

| Asset | Boundary | Required control |
|---|---|---|
| keeper key | local secret → Base Sepolia signer | disposable, low balance, never logged |
| owner key | human wallet → Guardian admin | separate from keeper; only human unpause |
| Graph endpoint/key | process environment → Graph gateway | secret scan; no endpoint logging |
| cursor/reservations | Graph source → durable store | atomic uniqueness and restart recovery |
| incident reference | detector → contract event | canonical deterministic hash |
| AI output | model/provider → policy | strict schema; low confidence fails closed |

## Primary abuse cases

1. **Compromised keeper attempts unpause.** Contract rejects it; keeper role has
   pause-only authority.
2. **Duplicate/replayed Graph entities create repeated transactions.** Canonical
   entity ID has a durable unique reservation; duplicates return prior outcome.
3. **Reorg invalidates a previously seen event.** Source rewinds confirmed cursor,
   replays a bounded window and deduplicates canonical IDs.
4. **RPC timeout after broadcast triggers a second send.** Tx hash/nonce are saved
   before waiting; timeout becomes `indeterminate` and reconciliation owns retry.
5. **Malicious or malformed AI output asks for action.** Schema validation,
   confidence threshold and deterministic policy refuse it; AI cannot call chain.
6. **False positive pauses the protocol.** Automation can only reduce availability,
   never move funds or unpause; owner follows an attributed manual recovery SOP.
7. **Notification failure hides the incident.** Durable outbox/tracked tasks expose
   retries and terminal failure independently of action success.
8. **Supply-chain compromise in Graph CLI.** CLI is pinned, local, unprivileged and
   restricted to trusted inputs; current audit advisories remain documented.
9. **Secret leakage through logs/demo/history.** Values stay in ignored env files;
   output is allowlisted/redacted; working tree and full Git history are scanned.

## Safety invariants

- no mainnet chain ID or real-value account;
- no automated unpause;
- one canonical event → at most one reserved action;
- receipt timeout is never treated as definitive failure;
- success requires receipt status, confirmations and state re-read;
- invalid AI output cannot widen permission;
- every reset/unpause is human-attributed.

## Residual risks accepted for the prototype

- Graph/RPC availability and indexing latency;
- Base Sepolia reorgs and faucet instability;
- owner key compromise;
- protocol-wide denial of service from a false positive pause;
- unremediated transitive advisories in the pinned Graph CLI;
- SQLite/local-state loss unless backup and restore are demonstrated.

## Tests mapped to threats

| Threat | Minimum test |
|---|---|
| role escalation | keeper unpause reverts; owner unpause succeeds |
| replay/concurrency | simultaneous duplicate entity creates one reservation/tx |
| restart | crash after reserve and after broadcast reconciles safely |
| chain ambiguity | status=0, timeout and confirmation reorg have distinct outcomes |
| AI injection | malformed, adversarial and low-confidence outputs refuse action |
| notification loss | outbox retry survives process restart |
