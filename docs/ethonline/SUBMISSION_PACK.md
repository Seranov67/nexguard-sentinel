# NexGuard Sentinel ? ETHOnline 2026 Submission Pack

This document contains all verified text, onchain links, and partner details required for the **ETHGlobal Hacker Dashboard** submission and the **2?4 minute Demo Video**.

---

## 1. Project Information for ETHGlobal Dashboard

- **Project Title:** `NexGuard Sentinel`
- **Tagline:** Autonomous Circuit Breaker with Verifiable AI, The Graph Observability, and Ledger Clear Signing
- **Category:** Security / Continuity
- **Repository URL:** `https://github.com/Seranov67/nexguard-sentinel` (branch: `feature/ethonline-sentinel`)
- **Demo Video URL:** *[Insert YouTube / Loom link here: 2?4 min, >=720p, human narration]*

### Short Description (Markdown for Dashboard)
```markdown
NexGuard Sentinel is an autonomous, fail-closed incident response circuit breaker for DeFi vaults on Base Sepolia. It continuously monitors onchain withdrawals via The Graph Studio, extracts behavioral anomaly features, classifies exploits with a fail-closed AI classifier, and triggers onchain emergency pausing via Guardian.sol through a deterministic ActionPolicy.

Following an incident, an AI agent investigates the root cause via Bazantic MCP tools and the x402 Incident Evidence API, generating verifiable cryptographic proofs. Safe protocol recovery is guarded by human protocol owners using Ledger ERC-7730 Clear Signing, ensuring that automated keepers can only pause, never unpause.
```

---

## 2. Selected Partner Tracks & Submission Details

### Partner 1: The Graph
- **Prize Track:** *Best AI Tooling or AI Use Case with The Graph (Continuity)* ($15,000 pool)
- **Why it's load-bearing:** The Graph is the real-time observability backbone. Without the Subgraph, Sentinel has no awareness of onchain state.
- **Studio Subgraph Endpoint:** `https://api.studio.thegraph.com/query/1758726/nexguard-sentinel/v0.1.0`
- **Deployment ID:** `QmNcPyyo2Ybz1M3Lmg1eAE8A6ATuhZ3RvqePiks18fTfcQ`
- **Indexed Contract:** `DemoVault.sol` (`0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13` on Base Sepolia)
- **Partner Description for Form:**
```markdown
The Graph Studio provides real-time, low-latency (<3s) event indexing for NexGuard Sentinel. Our custom Subgraph tracks all withdrawal events from DemoVault on Base Sepolia. The Sentinel event loop ingests confirmed Graph entities, feeds sliding-window velocity and volume features into our AI classifier, and advances a deterministic, durable SQLite cursor. Removing The Graph completely breaks the automated detection and response pipeline.
```

### Partner 2: Bazantic
- **Prize Track:** *Help an Agent Use Your Hackathon Project (Continuity)* ($1,000 pool)
- **Why it's load-bearing:** After the circuit breaker pauses the protocol, third-party agents and protocols need to know why. Bazantic tools provide this bridge.
- **Artifacts:**
  - `sentinel/evidence_api.py` (FastAPI with x402/MPP payment gate and SHA-256 state fingerprinting)
  - `sentinel/bazantic/mcp_server.py` (MCP tools: `get_latest_incident`, `verify_incident_evidence`)
  - `sentinel/bazantic/recipe.json` (Bazantic Recipe guiding agents through investigation)
  - `docs/ethonline/BAZANTIC_AB_BENCHMARK.md` (A/B Benchmark showing +3 quality improvement)
- **Partner Description for Form:**
```markdown
We built a complete Bazantic agent integration to enable autonomous post-incident investigation. Sentinel exposes an Incident Evidence API protected by an x402 micro-payment gate. Through our Bazantic MCP Server and structured Recipe, AI agents can pay for, query, and verify cryptographic SHA-256 proof of why the circuit breaker was triggered, explaining the exploit mechanism in plain English with 4/4 benchmark accuracy.
```

### Partner 3: Ledger
- **Prize Track:** *Continuity* ($1,500 pool)
- **Why it's load-bearing:** Enforces the fundamental security invariant: keepers can only pause; only the human owner with hardware confirmation can unpause.
- **Artifacts:**
  - `sentinel/ledger/erc7730_unpause.json` (ERC-7730 Clear Signing metadata descriptor for `Guardian.unpause(bytes32)` on Base Sepolia)
  - `sentinel/ledger/unpause_ledger.py` (CLI with `--simulate` and `--dry-run` modes)
  - `sentinel/ledger/keyring_helper.py` (`wallet-cli ring` Ledger Agent Stack integration)
- **Partner Description for Form:**
```markdown
Ledger provides the critical recovery anchor for NexGuard Sentinel. While automated keepers can rapidly pause a compromised vault, they are strictly forbidden from unpausing. We implemented an ERC-7730 Clear Signing descriptor for Guardian.unpause(bytes32) on Base Sepolia (Chain 84532), enabling human protocol owners to visually verify the incident resolution on their Ledger hardware screen before restoring liquidity.
```

---

## 3. Verified Base Sepolia Onchain Evidence

| Asset / Action | Address or Transaction Hash | Basescan Link |
|---|---|---|
| **Guardian Contract** | `0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3` | [View Guardian on Basescan](https://sepolia.basescan.org/address/0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3) |
| **DemoVault Contract** | `0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13` | [View DemoVault on Basescan](https://sepolia.basescan.org/address/0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13) |
| **Exploited Withdrawal** | `0x05e2c2fad8422867dc97587bb9f4fd8516f616ed41ecd30469738a221d1ae35e` | [View Exploit Tx](https://sepolia.basescan.org/tx/0x05e2c2fad8422867dc97587bb9f4fd8516f616ed41ecd30469738a221d1ae35e) |
| **Autonomous Pause Tx** | `0xaa915ea5e86823ec63259d3573b05c4e243fbbaae3ae3a8003dbaf8582e29d75` | [View Pause Tx](https://sepolia.basescan.org/tx/0xaa915ea5e86823ec63259d3573b05c4e243fbbaae3ae3a8003dbaf8582e29d75) |
| **Owner Recovery Unpause** | `0x2f68bdd881089057139f38d1ce7585169d27ff793f5b7af5a34951def628b070` | [View Unpause Tx](https://sepolia.basescan.org/tx/0x2f68bdd881089057139f38d1ce7585169d27ff793f5b7af5a34951def628b070) |

---

## 4. 3-Minute Demo Video Script (Storyboard)

**Rules Reminder:**
- Length: strictly between **2:00 and 4:00 minutes** (aim for ~3:00).
- Resolution: >= 720p (recommend 1080p).
- Voice: **Human narration only** (no AI voice / TTS allowed by ETHGlobal).
- Screen: Hide all private keys or `.env` files.

### Scene 1: Introduction & The Problem (0:00 ? 0:40)
- **Screen:** Title slide or IDE showing architecture diagram: `WATCH -> DETECT -> DECIDE -> ACT -> PROVE -> RECOVER`.
- **Narration:**
  > "Hello! Today DeFi protocols lose billions because onchain exploits unfold in seconds, while human emergency response takes hours.
  > 
  > Introducing **NexGuard Sentinel** ? an autonomous, verifiable circuit-breaker system for smart contracts built for ETHOnline 2026.
  > Sentinel unites three load-bearing partners: **The Graph** for real-time observability, **Bazantic** for agentic incident investigation, and **Ledger** for hardware-secured recovery."

### Scene 2: Live Exploit & The Graph Indexing (0:40 ? 1:20)
- **Screen:** Terminal running `python scripts/trigger_exploit.py` and The Graph Studio dashboard.
- **Narration:**
  > "Here on Base Sepolia, we have our DemoVault contract protected by Guardian.sol.
  > An attacker initiates an unauthorized flash withdrawal draining 25 ETH.
  > Notice how immediately **The Graph Studio** indexes this confirmed event with sub-3-second latency. The Graph gives Sentinel the clean, structured entity stream necessary for real-time detection."

### Scene 3: AI Classification & Autonomous Pause (1:20 ? 2:00)
- **Screen:** Terminal running `python -m sentinel.cli run --once` and then Basescan showing `Guardian.pause()`.
- **Narration:**
  > "Now our Sentinel event loop ingests the Graph event.
  > Our fail-closed AI classifier extracts velocity and volume features and flags the transaction as a critical threat.
  > Our deterministic ActionPolicy authorizes the emergency action, and Sentinel broadcasts `Guardian.pause()` directly on Base Sepolia.
  > Let's check Basescan: Guardian is now PAUSED, and any subsequent withdrawal is blocked with the `GuardianPaused` error. The vault funds are saved!"

### Scene 4: Bazantic Agent Investigation (2:00 ? 2:40)
- **Screen:** Terminal showing Bazantic Recipe and MCP response or running `python -m sentinel.bazantic.benchmark_ab`.
- **Narration:**
  > "Now that the vault is paused, how do external agents know what happened?
  > Here comes **Bazantic**. Sentinel exposes an Incident Evidence API behind an x402 payment gate.
  > Using our Bazantic Recipe and MCP server, an autonomous AI agent pays for the incident evidence, verifies the SHA-256 state fingerprint, and produces a plain-English incident post-mortem explaining the exploit vector with 100% benchmark fidelity."

### Scene 5: Ledger Clear Signing & Recovery (2:40 ? 3:20)
- **Screen:** Terminal running `python -m sentinel.ledger.unpause_ledger --simulate` showing the simulated Ledger screen.
- **Narration:**
  > "Finally, protocol recovery. In Sentinel, automated keepers can only pause ? they can NEVER unpause.
  > Only the human owner can restore protocol liquidity.
  > Using **Ledger ERC-7730 Clear Signing**, the owner verifies the contract address, action, and verified resolution hash directly on their hardware wallet screen before broadcasting `Guardian.unpause()`.
  > Sentinel brings together speed for safety, and hardware human verification for recovery."

### Scene 6: Conclusion (3:20 ? 3:30)
- **Screen:** GitHub repository, test suite passing (102/102 tests).
- **Narration:**
  > "All 102 tests are passing, and all contracts are verified on Base Sepolia.
  > Thank you, and welcome to the future of onchain autonomous resilience with NexGuard Sentinel!"
