# Base Sepolia deployment handoff

**Recorded:** 2026-09-04  
**Resume:** 2026-09-05  
**Purpose:** fund the disposable deployer, deploy the contracts, and publish the
NexGuard Sentinel Subgraph.

## Current verified state

### Update: 5 September 2026

Funding and ES102 deployment are complete. Do not repeat the transfer or deployment.
Public receipts and verified contract state are recorded in
`deployments/base-sepolia.json`.

- Guardian: `0x8B7B1Ee7e335FD00F35cc6272C113c8735cB8Ed3`, block 46427864.
- DemoVault: `0xF1683d32fEF59BBB95483561aBa62a1bdA65Cd13`, block 46427865.
- Both receipts succeeded; bytecode, at least three confirmations, owner, keeper,
  initial unpaused state, and Vault-to-Guardian link were verified.
- An immediate Vault RPC call returned empty data; a later read verified the
  existing deployment successfully, without sending any replacement transactions.
- The Subgraph manifest now uses the verified address and start block.
- Verification passed: 55 Python tests, 9 Solidity tests, 1 Matchstick test,
  Graph codegen/build, Ruff, strict MyPy, and Compose configuration.
- ES201 complete: Studio `nexguard-sentinel` v0.1.0 deployed and a real Withdrawal
  was verified against its receipt, canonical ID, block hash and sequence.
  Evidence: `deployments/subgraph-studio.json`. Query latency was 697 ms; first
  observed appearance was at most 31 seconds after the event block (includes
  verification delay; not an exact indexing latency).
- Studio deployment is available for development queries; decentralized-network
  publication via the Studio Publish button has not been performed.
- ES301 complete: environment configuration and SQLite durable core; 19 Sentinel
  tests and 55 existing tests pass, including a separate-process crash after nonce
  persistence, concurrent reservations and transactional failure rollback.
- Next: ES302 ingestion, deterministic policy, executor and reconciliation.
  Automatic pause, AI classification and notification delivery remain pending.

The funding instructions below are retained as the historical 4 September handoff.

- ETHGlobal participation is confirmed and the Continuity Track is selected.
- The event branch is `feature/ethonline-sentinel`.
- Guardian and DemoVault are implemented and locally verified with 9 Foundry
  tests and 5 deployment-tool tests.
- The Subgraph passes code generation, WebAssembly compilation, and its
  Matchstick mapping test.
- The official public Base Sepolia RPC responds with chain ID `84532`.
- ETHGlobal faucet transaction
  `0xce439e827fad4c0cb8b8735e3630e68c8dd25d6e08bf2c39c7de54b8f4cb7c0c`
  sent 0.1 test ETH to the participant's verified wallet.
- Disposable private keys exist only in ignored `.env.ethonline`. They must
  never be pasted into chat, committed, or reused with real assets.

## Wallets and network

| Role | Public address |
|---|---|
| Participant faucet wallet | `0xd465275265832c95a4c3e89d932132d23e5defa5` |
| Disposable keeper/deployer | `0x46C3a46Efd54f928707F83D9e3F5f87f0D420172` |
| Disposable human-owner role | `0xcF44200ba4024772acF529D87B758C4FCA6e7A15` |

Base Sepolia settings:

- Network name: `Base Sepolia`
- RPC URL: `https://sepolia.base.org`
- Chain ID: `84532`
- Currency symbol: `ETH`
- Explorer: `https://sepolia.basescan.org`

## Owner action required tomorrow

1. Open the wallet used to verify ETHGlobal.
2. Confirm the active address is
   `0xd465275265832c95a4c3e89d932132d23e5defa5`. Stop if it differs.
3. Switch to **Base Sepolia**, not Base Mainnet or Ethereum Mainnet.
4. Confirm the wallet shows approximately 0.1 test ETH.
5. Select **Send**.
6. Paste recipient `0x46C3a46Efd54f928707F83D9e3F5f87f0D420172`.
7. Enter `0.01 ETH`.
8. Recheck Base Sepolia, the recipient ending in `0172`, and the amount.
9. Confirm the testnet transaction and retain its transaction hash.
10. Tell Codex `готово` and optionally provide the public transaction hash.

Never disclose a seed phrase or private key. No real ETH is required or allowed
for this project.

## Codex continuation checklist

After the transfer is confirmed onchain:

1. Read the disposable deployer balance through the public RPC.
2. Build the pinned Solidity artifacts and execute `contracts/deploy.py` with
   public evidence output.
3. Verify chain ID, receipts, bytecode, Guardian owner/keeper state, initial
   unpaused state, and the DemoVault-to-Guardian link.
4. Record contract addresses, blocks, transaction hashes, and explorer links.
5. Insert the verified DemoVault address and deployment block into the Subgraph
   manifest, then rerun codegen/build/Matchstick tests.
6. Ask the owner only for the account-bound Subgraph Studio wallet connection,
   Subgraph creation, and deploy key when that gate is reached.
7. Deploy the Subgraph, generate a real valueless Withdrawal, query it with
   `_meta`, and record indexing latency.
8. Mark ES102 and ES201 complete only after their live evidence is verified.

## Local verification snapshot

- Python: 55 tests passed; Ruff passed; strict MyPy passed.
- Solidity: 9 tests passed; formatting and compilation passed.
- Subgraph: codegen/build passed; Matchstick 0.6.0 test passed 1/1.
- Compose configuration passed.
- Gitleaks working-tree and full-history scans passed.

Temporary Foundry root-level `cache/` and `out/` artifacts were removed; they
are generated files and can be recreated by the pinned build.
