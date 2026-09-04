# AI prompt and specification register

ETHGlobal requires prompts and planning artifacts to be included when a
spec-driven AI workflow is used. This register records prompts available to this
workspace without inventing or reconstructing wording that was not preserved.

## Codex prompts preserved verbatim

| Date | Verbatim user prompt | English translation | Resulting areas |
|---|---|---|---|
| 2026-09-03 | `зроби повний аудит проекту і проаналізуй і побудуй план дій` | Perform a full project audit, analyze it, and build an action plan. | Full audit and recovery plan |
| 2026-09-03 | `ок виконуй` | OK, execute it. | Phase 0 documentation, spike hardening, toolchain and verification |
| 2026-09-03 | `задокументуй все вірно по правилах` | Document everything correctly according to the rules. | Rule verification, compliance register, disclosure and submission documentation |
| 2026-09-04 | `так продовжемо роботу над проекто і зверни увагу ти пишеш коменти на укр мові але ми робимо для конкурсу і напевно потрібно на анг мові, пеервір і надай мені результат` | Continue the project, review the Ukrainian comments because the competition materials should probably be in English, and report the result. | English conversion of source comments, CLI output, and judge-facing documentation |
| 2026-09-04 | `сьогодні той день коли потрібно починати наш проект, план дій на весь період до подання` | Today is the day to start our project; provide the action plan for the entire period until submission. | Updated execution plan and Dashboard verification workflow |
| 2026-09-04 | `так` / `робимо` / `так є` / `так вперед` | Yes / Let's do it / Yes, it is there / Yes, go ahead. | Authenticated Dashboard verification, baseline tag and event branch, imported provenance package, and proposed ETHOnline SSD Stage 0 |

System/developer instructions supplied by the Codex environment are platform
configuration, not authored project prompts. The final submission should use the
product's supported conversation export/share mechanism if judges need the full
assistant transcript; do not manually fabricate omitted turns.

## Earlier AI sessions

Claude assisted the initial preparation documents before 3 September. Exact raw
prompts are not currently present in this workspace. This is an explicit evidence
gap, not a claim that no prompts existed.

Before submission, do one of the following:

1. export and include the exact relevant Claude prompt/session history; or
2. clearly state that the raw prompts were not retained and include every surviving
   spec, plan and generated artifact with its pre-event provenance.

Option 1 is preferred. Never backfill approximate prompts as verbatim history.

## Event-period logging rule

For every material AI-assisted event change, append:

- timestamp and tool/model;
- exact user-authored task prompt or a link to the exported transcript;
- files/areas changed;
- what the human reviewed, changed or verified;
- test/live evidence;
- whether generated output was accepted, modified or rejected.
