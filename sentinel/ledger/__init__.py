"""NexGuard Sentinel -- Ledger integration package.

Provides hardware-enforced owner recovery for the Guardian circuit-breaker:
  - ERC-7730 Clear Signing metadata for Guardian.unpause()
  - unpause_ledger.py: owner CLI with --simulate mode (no physical device required)
  - keyring_helper.py: wallet-cli ring secret management integration
"""
