# NexGuard Sentinel — project identity

Updated after owner-authorized plan reconciliation on 2026-09-06.

| Item | Canonical value |
|---|---|
| Product / submission name | NexGuard Sentinel |
| Event documentation title | NexGuard Sentinel — ETHOnline 2026 |
| Primary event workspace | `D:\NexGuard Sentinel` |
| GitHub repository | `Seranov67/nexguard-sentinel` |
| Event branch | `feature/ethonline-sentinel` |
| Separate legacy checkout | `D:\nexguard-edge-resilience` |
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

## Current delivery boundary

ES302, ES401 and ES402 are implemented and locally verified. ES501 live model-backed
evidence and ES502 final submission remain open. Historical preparation records do
not override the current task list or FINAL_AUDIT_2026-09-06.md.
