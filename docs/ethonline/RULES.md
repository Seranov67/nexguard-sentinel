# ETHOnline 2026 — verified rules and project controls

> Last verified: 3 September 2026, Europe/Kyiv. This file separates public
> organizer requirements, partner-specific requirements, Dashboard-only facts,
> and stricter internal controls.

## Authoritative sources

1. ETHGlobal rules, submission and judging:
   <https://ethglobal.com/events/ethonline2026/info/details>
2. ETHOnline 2026 partner prizes:
   <https://ethglobal.com/events/ethonline2026/prizes>
3. Authenticated Hacker Dashboard: source of participant-specific status,
   check-in forms and any schedule fields not visible on the public pages.

If these sources change, the source page and Dashboard override this document.
Record the change date instead of silently rewriting historical evidence.

## Public ETHGlobal requirements — confirmed

| Requirement | Exact project interpretation |
|---|---|
| Submission deadline | 13 September 2026, 12:00 pm EDT = 19:00 Europe/Kyiv |
| Submission route | Hacker Dashboard; project title, description and repository link |
| Demo video | Required; 2–4 minutes; upload rejects under 2 or over 4 minutes |
| Video format | At least 720p; no speed-up, mobile-phone recording, or TTS/AI voiceover |
| Partner selection | Up to 3 partner prizes; selection in the form is required for partner review |
| Continuity | Existing codebase/product is allowed under the selected Continuity track |
| Prior work | Clearly document what existed before and what was built during the event |
| Version control | Track work throughout the event; large single commits or missing history may disqualify |
| Reuse | Open-source libraries/starter kits are allowed with transparent attribution |
| Evidence | Include repository/Figma/equivalent evidence that distinguishes new and reused work |
| AI assistance | Allowed, but files/areas and manner of use must be documented |
| Human contribution | Entirely AI-created work without meaningful team contribution may lose eligibility |
| Spec-driven work | If used, include all specs, prompts and planning artifacts in the submission repo |
| Judging | Technicality, originality, practicality, usability and WOW factor |
| Finalist session | If selected: 4-minute demo plus 3-minute Q&A |

The public details page lists the event dates but does not provide a reliable
public hacking-start timestamp in the rules text. The current project boundary
of **4 September, 19:00 Kyiv** is therefore a conservative planning assumption,
not quoted as a public rule. Before the first event commit, verify the start in
the authenticated Dashboard/event schedule and record it in `COMPLIANCE.md`.

## The Graph AI/Continuity requirements — confirmed

Selected pool: **Best AI Tooling or AI Use Case with The Graph (Continuity)**.

| Partner requirement | Sentinel evidence required |
|---|---|
| The Graph is load-bearing | Runtime consumes live Subgraph/Substreams data; removing Graph breaks the demonstrated flow |
| Live provider data | Studio/API-key or The Graph Market endpoint; no mock/local/static-only qualification claim |
| Meaningful use | Graph-derived data drives classification, decision or automation—not raw printing only |
| Correct pool | Existing project/product is extended; submit to Continuity, not From Scratch |
| Open source | Public repository with a clear runnable README or relevant SKILL.md |
| Demo | Public 2–4 minute demonstration of the working integration |
| Prior-work disclosure | Baseline commit/tag and explicit prior/new table |

A single custom Subgraph without composition or standardized schema does **not**
qualify for the separate composable/standardized track. Sentinel applies only to
the AI/Continuity pool unless the architecture materially changes and is proven.

## Dashboard-dependent facts — not yet confirmed

- exact hacking-start timestamp;
- check-in availability, deadlines and required fields;
- team roster and eligibility state;
- final submission form fields;
- live-judging selection and assigned session.

Do not describe any of these as completed or mandatory until observed in the
authenticated Dashboard. Capture the date and result in `COMPLIANCE.md`.

## Internal controls — stricter than organizer rules

These are project policy, not claimed ETHGlobal disqualification rules:

1. No product commit before the Dashboard-confirmed hacking start.
2. Tag the verified last pre-event commit and preserve the full history.
3. Keep `DISCLOSURE.md`, `AI_USAGE.md`, `AI_PROMPTS.md` and licenses current.
4. Use a disposable, faucet-funded Base Sepolia wallet; no mainnet or real value.
5. Automatic authority is pause-only; owner/human alone may unpause.
6. Never log, commit, screenshot or paste private keys, deploy keys or API tokens.
7. Run working-tree and full-history secret scans before public push/submission.
8. Submit internally by 17:00 Kyiv on 13 September; 19:00 Kyiv is the hard deadline.
9. Do not claim a deployment, latency, test result, check-in or ticket without evidence.

## Secret and publication gate

Run in the actual submission Git repository:

```powershell
gitleaks dir . --config .gitleaks.toml --redact --no-banner
gitleaks git . --config .gitleaks.toml --redact --no-banner
git log --all --full-history -- .env .env.local secrets.json
rg -n '(PRIVATE_KEY|GRAPH_DEPLOY_KEY|TELEGRAM_BOT_TOKEN)\s*=\s*\S+' .
```

Also run a private denylist scan for known sensitive wallet/account identifiers.
Never store the denylist value itself in the public repository or CI logs.
