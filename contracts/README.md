# NexGuard Sentinel contracts

These contracts are event-period work for ETHOnline 2026 and are intentionally
limited to Base Sepolia demonstrations. `DemoVault` holds no Ether or tokens; its
public credit ledger and `unsafeWithdrawFrom` function are deliberately insecure
fixtures used to generate observable withdrawal incidents.

`Guardian` separates authority:

- owner configures keepers and is the only account allowed to unpause;
- keeper can pause only;
- every incident reference is one-use;
- pause and unpause transitions emit attributed audit events.

Run the self-contained tests with Foundry:

```bash
cd contracts
forge fmt --check
forge test -vvv
```

For Base Sepolia deployment, copy `.env.ethonline.example` to the ignored
`.env.ethonline`, populate it locally, build artifacts, and run:

```bash
cd contracts
forge build
cd ..
python contracts/deploy.py --evidence docs/ethonline/deployments/base-sepolia.json
```

The deployment script refuses non-Base-Sepolia RPCs, never prints the private
key, uses EIP-1559 transactions, verifies successful receipts, and re-reads the
configured owner, keeper, initial pause state, and Vault-to-Guardian link.

Never deploy these contracts to mainnet or use them with assets of value.
