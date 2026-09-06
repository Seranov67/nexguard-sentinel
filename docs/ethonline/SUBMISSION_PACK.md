# NexGuard Sentinel — submission and recording pack

Status: reviewable draft, not a submitted project. Updated 6 September 2026 after
code audit. Claims below distinguish implementation, historical receipts and pending
live demonstrations. Do not add AI, payment or hardware claims without new evidence.

## Dashboard text

**Title:** NexGuard Sentinel

**Tagline:** Testnet circuit breaker with Graph observability and auditable pause-only automation.

**Track:** Continuity; pre-existing work is disclosed in DISCLOSURE.md.

**Repository:** https://github.com/Seranov67/nexguard-sentinel/tree/feature/ethonline-sentinel

**Demo video:** PENDING — requires human narration, recording and a public/unlisted URL.

**Short description:**

NexGuard Sentinel is a Base Sepolia incident-response prototype. A live The Graph
Subgraph indexes withdrawals from a deliberately vulnerable, valueless DemoVault.
Sentinel extracts bounded rolling features, requests a structured AI assessment,
and applies deterministic pause-only policy. SQLite reservations, persisted signed
transaction hashes, canonical receipts and confirmation checks make the action
path auditable and prevent blind resends. Missing or invalid AI cannot authorize
an action. Only the separate human owner can unpause.

An Evidence API and MCP tools expose recorded incident data and payload integrity
checks. A Ledger recovery CLI and schema-validated ERC-7730 descriptor support
recovery preparation. A new real-model live pause and no-resend reconciliation
were verified on 6 September. Payment settlement and hardware Clear Signing
remain unverified.

**How it is built:**

Python 3.12, SQLite, httpx, FastAPI, web3/eth-account, Ollama structured output,
Solidity Guardian/DemoVault on Base Sepolia, and a Graph Studio Subgraph.
The pre-existing IoT resilience MVP is preserved alongside the new Sentinel
module. New event work and AI assistance are documented in the SSD and disclosure
records. Tests exercise duplicate/concurrent delivery, restart, failed AI,
confirmation timeout, reorg, state mismatch and durable notification retries.

**The Graph partner description:**

Graph Studio is the runtime source for withdrawal entities. Sentinel validates
provider deployment, snapshot metadata, canonical block hash, confirmation window,
ordering and entity identity before persistence. Removing Graph ingestion removes
the live signal. The Ollama classification path consumes only bounded features
computed from this data. On 6 September, a new indexed withdrawal was classified
by Qwen3, producing one pause transaction. Initial RPC uncertainty triggered a latch;
separate reconciliation verified receipt, confirmations and paused state without
a second send. Restart produced no additional action.

**Bazantic partner description:**

We provide a Recipe, stdio MCP tools and an Incident Evidence API for agent
investigation. Tools retrieve persisted incidents and independently recompute
payload fingerprints. The A/B runner uses a real model, identical task/settings
and the same read-only tools; only Recipe guidance differs. Its real-model run
is pending. x402 is a payment prototype, not settled payment infrastructure;
unverified proofs are rejected and local demo access requires server opt-in.

**Ledger partner description:**

Our ERC-7730 descriptor for Guardian.unpause(bytes32) validates against a pinned
official schema. The CLI constructs Ethereum Keccak-256 calldata and checks the
hardware-derived address against the deployed owner before using cast --ledger.
Terminal previews are explicitly simulations. Device rendering, Clear Signing
support and a hardware-signed recovery are not yet demonstrated.

Select partner prizes only after reviewing these limitations against current
qualification requirements. No partner selection is recorded as complete.

## Public onchain references

New real-model rehearsal: withdrawal `0x0867c938ef6038749b4142c77beb1778e315ce180010a0ffbe39b464caafbe31`
at block 46474498; pause `0x26f2076b9dc3c1e7313f68cd0506e393e38a11a4680b06eb6a558bd77b59a750`
at block 46474539. The Guardian is currently paused; owner recovery is separate.


- Guardian: `0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3`
- DemoVault: `0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13`
- Withdrawal: `0x05e2c2fad8422867dc97587bb9f4fd8516f616ed41ecd30469738a221d1ae35e`
- Historical pause: `0xaa915ea5e86823ec63259d3573b05c4e243fbbaae3ae3a8003dbaf8582e29d75`, block **46433932**
- Historical owner unpause: `0x2f68bdd881089057139f38d1ce7585169d27ff793f5b7af5a34951def628b070`, block **46434002**
- Graph endpoint: https://api.studio.thegraph.com/query/1758726/nexguard-sentinel/v0.1.0

Use https://sepolia.basescan.org/tx/ followed by the full transaction hash.
These receipts are historical and do not independently prove AI or Ledger use.
The 25 units consumed by the demo are valueless accounting credits, not Ether.

## Recording plan — target 3:00–3:30

Record desktop capture at 1080p with your own voice. Do not show environment
files, private keys or wallet secret screens. Keep the visible label “Base Sepolia —
valueless demo credits”. Cut waiting periods; do not speed up narration.

| Time | Screen | Narration topic |
|---|---|---|
| 0:00–0:25 | README flow and testnet label | Problem and pause-only design |
| 0:25–1:00 | Graph query plus withdrawal receipt | Real source; explain demo credits |
| 1:00–1:50 | Recorded live classification and new pause receipt | AI boundary, reservations, confirmation checks; show the recorded latch and successful reconciliation |
| 1:50–2:25 | Evidence API/MCP response | Recorded cause and integrity; disclose payment prototype |
| 2:25–2:55 | Ledger `--simulate` | Owner-only recovery; clearly label terminal simulation |
| 2:55–3:20 | Tests, repository and limitations | What is implemented; what still needs live evidence |

### Human narration draft

Hello, I am presenting NexGuard Sentinel, a testnet circuit breaker for smart
contracts. It explores how automated incident response can stop activity quickly
while leaving a record that an operator can inspect. Automated keepers may pause,
but they can never restore activity themselves.

This DemoVault is deployed on Base Sepolia and deliberately contains an unsafe
withdrawal method. It uses valueless accounting credits. No Ether or user tokens
are held in the vault. Here is a real withdrawal event indexed by our Graph Studio
Subgraph. The Graph provides the structured event stream used by Sentinel.

The ingestion path checks the deployment identity, canonical snapshot, confirmation
window and event ordering. It stores events separately from their processing state,
so a restart after ingestion does not silently lose work. Rolling features summarize
volume, velocity and actor diversity without sending arbitrary event text to a model.

The AI client requests a bounded, structured assessment. Missing or malformed output
cannot authorize a transaction. Deterministic policy then checks the latch, action
limits and durable reservation. The signer stores its transaction hash before
broadcast. A success requires a canonical receipt, sufficient confirmations and a
fresh paused-state read. Here is the new live pause receipt at block 46474539. The first RPC verification
was uncertain, so the system latched. Reconciliation confirmed the same transaction
without another send, and a separate process restart produced no new action.

For investigation, the Evidence API exposes the recorded incident and its transaction
reference. MCP tools let an agent retrieve the record and recompute its fingerprint.
This checks payload integrity, not independent chain authenticity. Payment settlement
is a prototype and is not claimed as completed. The comparison runner records actual
model tool calls rather than inventing a score improvement.

Recovery belongs to the human owner. This terminal view is a simulation of our Ledger
recovery preparation. The descriptor passes the official schema, and the CLI checks
the hardware-derived owner address before sending. A real device Clear Signing
demonstration still needs to be recorded.

The repository includes safety tests, reproducible dependencies and a disclosure of
the older IoT project. Sentinel is an inspectable testnet prototype, with its remaining
live evidence clearly identified. Thank you.

### Commands to capture

```bash
python -m sentinel.cli status
python -m sentinel.cli run --once --dry-run
python -m sentinel.ledger.unpause_ledger --simulate --reason "Incident reviewed"
python -m pytest -q
```

After the model is available, record the real classification trace and replace only
the corresponding pending statement. For a new onchain rehearsal use `run --once`
without `--dry-run` only with the approved disposable keeper and a reviewed live
state. Do not present a historical transaction as a result of the repaired code.

## Submission completion checklist

- [x] Real model endpoint/name configured and live trace recorded; numeric wording limitations documented.
- [x] Final Graph-to-AI-to-pause rehearsal and restart evidence recorded.
- [ ] Real-model A/B transcript reviewed; unsupported partner claims excluded.
- [ ] Ledger hardware evidence obtained, or simulation limitation retained.
- [ ] Human voice recorded, desktop footage captured, exported at 720p or higher.
- [ ] Video duration is 2–4 minutes and link opens without authentication.
- [ ] Dashboard fields and up to three partner choices reviewed by owner.
- [ ] Dashboard submission confirmation and URL recorded.

Official requirements checked 6 September:
[ETHOnline submission rules](https://ethglobal.com/events/ethonline2026/info/details).
Deadline is 13 September 2026, 12:00 EDT / 19:00 Europe/Kyiv. The official rules
require a 2–4 minute video, at least 720p, and prohibit AI/TTS voiceover.

## Owner dependencies confirmed 6 September

The owner approved a local Docker Ollama installation. No Ledger is connected and
no human voice recording is available. Hardware evidence and final video remain
open; terminal simulation and AI-generated narration cannot close those tasks.

Evening Dashboard update could not be applied: browser automation failed to start
with a local kernel-assets error, including after reset. The earlier saved draft
remains; paste the current descriptions above before final submission.
