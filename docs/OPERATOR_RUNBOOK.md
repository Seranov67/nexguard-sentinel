# NexGuard Sentinel ? Operator Runbook & Incident Response Guide

This document is the standard operating procedure (SOP) for protocol security officers, DevOps engineers, and keeper operators running **NexGuard Sentinel** in production or testnet environments.

---

## 1. Environment & Configuration Reference

Sentinel reads configuration from environment variables or `.env.ethonline`:

| Variable | Required | Example / Default | Description |
|---|---|---|---|
| `RPC_HTTP` | **Yes** | `https://sepolia.base.org` | High-reliability JSON-RPC endpoint |
| `CHAIN_ID` | **Yes** | `84532` | Target EVM chain ID (Base Sepolia = 84532) |
| `GUARDIAN_ADDRESS` | **Yes** | `0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3` | Deployed Guardian contract |
| `VAULT_ADDRESS` | **Yes** | `0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13` | Protocol Vault contract to protect |
| `SUBGRAPH_URL` | **Yes** | `https://api.studio.thegraph.com/query/...` | The Graph Studio Query endpoint |
| `KEEPER_PRIVATE_KEY` | Conditional | `0x...` (64 hex characters) | Private key for pause broadcaster (keep in HSM/Vault) |
| `SENTINEL_STATE_PATH` | No | `.sentinel/state.sqlite3` | Filesystem path for durable SQLite database |
| `SENTINEL_CONFIRMATIONS` | No | `1` (testnet), `12` (mainnet) | Number of block confirmations before success |

---

## 2. Daily Health Checks & Monitoring

### 2.1 Check System Status
Run the operational status command:
```bash
python -m sentinel.cli status
```
**Expected Output:**
```text
==================================================
  NexGuard Sentinel -- System Status
==================================================
Chain ID:           84532 (Base Sepolia)
Guardian Contract:  0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3
Vault Contract:     0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13
State DB:           .sentinel/state.sqlite3
Safety Latch:       [NORMAL] (Not latched)
Cursor Sequence:    46433924000168 (Block: 46433924)
Guardian Status:    ACTIVE (Unpaused)
==================================================
```

### 2.2 Health-Check API
If running the Incident Evidence API service:
```bash
curl -s http://localhost:8000/health | jq .
```
Expected response: `{"status": "healthy", "database_reachable": true, "latest_incident_id": "inc_..."}`.

---

## 3. Running the Sentinel Control Loop

### 3.1 Single Test Step (Dry Run)
Simulates event ingestion, feature classification, and policy evaluation without broadcasting onchain:
```bash
python -m sentinel.cli run --once --dry-run
```

### 3.2 Continuous Daemon Mode
Runs the continuous event loop, polling The Graph every 10 seconds:
```bash
python -m sentinel.cli run
```

---

## 4. Incident Response & Latch Resolution

### 4.1 When the Safety Latch Trips
If `sentinel status` indicates `Safety Latch: [LATCHED]`:
1. **Identify the Cause**:
   Check the reason printed by `sentinel status`:
   - *Receipt Timeout*: RPC provider lagged after transaction broadcast.
   - *State Verification Mismatch*: Transaction confirmed, but onchain read did not reflect `paused == true`.
   - *Invalid Calldata / Gas Price Spike*: RPC rejected format or network congested.
2. **Inspect the Intent in SQLite**:
   ```bash
   python -m sentinel.cli reconcile <INTENT_ID>
   ```
3. **Verify Onchain Status on Basescan**:
   Look up the Keeper's recent transactions on Basescan to confirm if the pause succeeded.

### 4.2 Resetting the Latch (Audit Trail Required)
Once onchain truth is established, an authorized operator must reset the latch with their name and reasoning:
```bash
python -m sentinel.cli reset --operator "alice.sec" --reason "Confirmed pause tx 0xaa915... reached 12 block depth"
```
*Note: Every reset is permanently logged in the `audit` table with UTC timestamp and operator identity.*

---

## 5. Protocol Recovery & Unpausing (Owner SOP)

### Invariant: Keepers cannot unpause. Only the protocol owner can restore the circuit breaker.

1. **Verify Root Cause & Deploy Patch**:
   Ensure the smart contract exploit is remediated and no further drain is possible.
2. **Review Ledger Clear Signing Screen (Simulation Check)**:
   ```bash
   python -m sentinel.ledger.unpause_ledger --simulate --reason "Security audit passed: vulnerability patched"
   ```
3. **Connect Ledger Device and Execute Unpause**:
   Connect the hardware Ledger wallet and broadcast the attributed recovery transaction:
   ```bash
   python -m sentinel.ledger.unpause_ledger --reason "Security audit passed: vulnerability patched"
   ```
4. **Confirm Unpaused State**:
   ```bash
   python -m sentinel.cli status
   # Guardian Status must show: ACTIVE (Unpaused)
   ```
