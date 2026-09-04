# Attribution and reuse register

> Status: pre-event preparation. No file in this workspace is claimed as new
> event-period product implementation.

## Project-specific prior work

| Source | License/provenance | How it may be used | Required treatment |
|---|---|---|---|
| <https://github.com/Seranov67/nexguard-edge-resilience> | MIT; copyright © 2026 NexGuard Edge Resilience; baseline observed at `fa202e994a77ea365061f6ac609daea1b5ad60dd` | Continuity base repository; selected reliability concepts/code may be modified | Preserve full history, LICENSE and copyright; identify exact reused paths |
| <https://github.com/Seranov67/latch-agent> | MIT; copyright © 2026 Latch Agent Contributors; observed at `e9de4a4cfc457ed791eacb46bfdd53bba78a417d` | Design reference for reservation, reconciliation and latch behavior | Cite design influence; preserve license if any code is copied |
| <https://github.com/Seranov67/LLM-Log-Monitor> | Pre-existing project; no license reliance asserted here | Reference for operational prompting/structured output only | Copy no code unless its license and provenance are separately reviewed |

## Preparation artifacts

The audit, plans, specifications, config templates, demo prose, threat model,
write-path spike and The Graph spike were created or modified before the hacking
start, with Claude/Codex assistance documented in `AI_USAGE.md` and
`AI_PROMPTS.md`. If included in the submission, retain this pre-event label.

## Event-period attribution procedure

For every reused or adapted file, add a row before commit:

| Event file | Source repository/path + commit | Copied or adapted | License notice retained | New event changes |
|---|---|---|---|---|
| | | | | |

Do not describe an adaptation as written from scratch. Conversely, do not label
new event code as copied merely because it implements a previously documented
interface; record the actual relationship.

## Third-party packages

Python/npm/Solidity tools remain governed by their upstream licenses. Exact direct
versions and security status are recorded in `DEPENDENCIES.md`; lockfiles are the
machine-readable dependency evidence. Before publication, generate/review the
dependency license report and include notices required by any vendored assets.
