# NexGuard Sentinel — project identity

Confirmed for workspace preparation on 2026-09-05.

| Item | Canonical value |
|---|---|
| Product / submission name | NexGuard Sentinel |
| Event documentation title | NexGuard Sentinel — ETHOnline 2026 |
| Primary code workspace | `D:\nexguard-edge-resilience` |
| GitHub repository | `Seranov67/nexguard-sentinel` |
| Event branch | `feature/ethonline-sentinel` |
| Preparation materials | `D:\NexGuard Sentinel` |
| Previous IoT MVP | NexGuard Edge Resilience |

Use **NexGuard Sentinel** in event-facing descriptions. The local folder retains its existing name. On 5 September the owner selected
`Seranov67/nexguard-sentinel` as the new publication repository, preserving all
Git history and the baseline tag. The old remote is retained as `upstream`. Preserve the previous MVP's historical name in its specification,
architecture, and disclosure; the new publication repository retains the original project history.

## Where work belongs

| Path | Purpose |
|---|---|
| `contracts/` | Guardian and DemoVault contracts |
| `subgraph/` | The Graph schema, mappings, and component checks |
| `sentinel/` | Python Sentinel package and tests |
| `specs/002-ethonline-sentinel/` | Approved event requirements and staged tasks |
| `docs/ethonline/` | Disclosure, AI records, and deployment evidence |
| `services/`, `monitoring/`, `specs/001-nexguard-mvp/` | Existing IoT MVP |

Read the [event specification](../../specs/002-ethonline-sentinel/spec.md),
[task list](../../specs/002-ethonline-sentinel/tasks.md), and
[quality gates](../ssd/ETHONLINE_QUALITY_GATES.md) before implementation.
The [Constitution](../ssd/CONSTITUTION.md) records the approved scope amendment.

## Preparation boundary

This identity preparation changes documentation only. It does not certify final
submission readiness. The task list records ES302 (ingestion/policy/execution),
ES401 (AI), ES402 (notifications), and ES501–ES502 (live evidence and submission)
as outstanding. Follow their gates and stage approval workflow before advancing.
