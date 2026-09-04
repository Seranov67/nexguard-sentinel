# Contract evidence

## Local verification — 4 September 2026

- Foundry image: `ghcr.io/foundry-rs/foundry:stable`
- Resolved image digest:
  `sha256:043752653d5be351c71709091b3db97c4421c907eb40ea294195e7f532aadf46`
- Forge: 1.5.1 stable
- Solidity compiler: 0.8.24
- Format: PASS
- Compile: PASS
- Solidity tests: 9 passed, 0 failed, 0 skipped
- Python deployment-tool tests: 5 passed
- Full Python non-regression suite: 55 passed

Covered behavior:

- configured keeper can pause;
- keeper and outsider cannot unpause;
- outsider and revoked keeper cannot pause;
- owner can unpause with a nonzero reason hash;
- incident references cannot be reused;
- invalid severity refuses the transition;
- Demo Vault withdrawal is blocked while Guardian is paused;
- the intentional demo-only withdrawal vulnerability works before pause.
- owner and keeper addresses cannot be configured as the same account;
- deployment tooling refuses the wrong chain and identical owner/keeper roles;
- public deployment evidence is written atomically.

The deployment tool loads secrets only from the ignored `.env.ethonline`,
refuses any chain other than Base Sepolia, constructs EIP-1559 transactions,
checks receipt status, and re-reads role and Guardian/Vault linkage state.

## Live evidence pending

No Base Sepolia deployment is claimed yet. Record chain ID, owner and keeper
separation, contract addresses, deployment transaction hashes, pause/unpause
transactions, and explorer links only after a live run with a disposable,
faucet-funded testnet wallet.
