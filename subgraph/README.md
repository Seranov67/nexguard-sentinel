# NexGuard Sentinel subgraph

This subgraph indexes the valueless `DemoVault.Withdrawal` event on Base
Sepolia. Each immutable entity uses the transaction hash plus log index as its
canonical ID and includes a sortable block/log sequence for the Sentinel cursor.

## Local verification

```bash
npm ci
npm run codegen
npm run build
npm test
```

Matchstick publishes no native Windows binary. On this workstation the test was
also verified from WSL2 using the official Matchstick 0.6.0 Docker path; CI runs
the native Linux binary. The Graph CLI is a development-only tool and is not
shipped in the Sentinel runtime.

The pinned Graph CLI dependency tree currently reports 16 development-tool
advisories (1 critical, 10 high, 5 moderate). Do not run its archive/deploy
commands on untrusted inputs. Recheck the upstream CLI before publication and
record any version change with a fresh build and test result.

## Publish after ES102

1. Replace the zero address and `startBlock` in `subgraph.yaml` with the verified
   Base Sepolia DemoVault deployment values.
2. Run the local verification commands again.
3. Authenticate with the selected Graph provider using its secret manager or
   interactive CLI. Never commit a deploy key or private endpoint.
4. Publish, then record the public-safe Subgraph ID/version, an indexed block,
   and a redacted query/response in `docs/ethonline/COMPLIANCE.md`.

The manifest now targets the verified DemoVault deployment at block 46427865;
see `../docs/ethonline/deployments/base-sepolia.json`. A live provider deployment
is still required before ES201 can be complete.
