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

Never deploy these contracts to mainnet or use them with assets of value.
