# LoCT — Game Operations
Version: 0.1 | 2026-11-27 | Living document

## Purpose and decisions
Build a lightweight operations loop appropriate for a part-time solo developer: development → recruitment → playtest → analysis → improvement. Public Alpha should validate Strategic Discovery + Player Mastery rather than rely on daily rewards, grind or power creep. The September playtest plan specifies unique player names, recovery codes, stable UUIDs, device tokens and SQLite; implementation status requires verification.

## Proposed operating system
| Area | Responsibility |
|---|---|
| Acquisition | Channel management, recruitment and attribution |
| Activation | Onboarding, first battle start/completion and friction |
| Retention | Voluntary replay, return visits, team experimentation |
| Community | Feedback, moderation, patch notes and player discussion |
| Content | Hero spotlights, tactical clips and devlogs |
| LiveOps | Later optional weekly challenges, random encounters and tournaments |
| Support | Bug triage, account recovery and player communication |
| Revenue/referral | Later conversion and recommendations; no premature monetisation |

## Proposed telemetry and metrics
Record pseudonymous player ID, session, build version, acquisition source where available, battle start/end, stage, heroes, formation, result, rounds, duration, retry and return. Never log recovery codes or device secrets. Define privacy notice, retention policy and access controls before public collection.
- Activation: first battle starts / new players; first battle completions / first battle starts.
- Replay: players starting a second battle / first battle completers.
- D1/D7/D30: cohort members active on the specified day after first play / eligible cohort size; report sample sizes and time zone.
- DAU/MAU: unique active players per day/month; define activity as meaningful game interaction.
- Strategic discovery: distinct compositions, formation changes, retry after loss, hero usage and matchup-specific win rates (avoid interpreting small samples as balance proof).

## Proposed operations dashboard
Separate restricted admin view from player UI. Show cohort funnel, retention, battle counts, hero usage, errors and feedback. Start with simple exports/queries; build dashboard only when useful. Do not expose player secrets or personal data.

## Feedback workflow and cadence
Collect issue, build, reproduction steps, severity and optional comments. Triage blockers first; distinguish bugs, readability, balance and preferences. Review weekly, record decisions and compare subsequent cohorts. Reuse content across channels; defer scheduled LiveOps until capacity and demand justify it.

## Open questions
Verify existing telemetry and identity implementation, establish baseline metrics, define privacy obligations and dashboard scope. Roguelite mode is an exploratory idea, not a committed feature.

## Sources
2026-09-05 Online Playtest and Player Identity Strategy (including September 12 and October 8 updates); 2026-09-13 Game Retention Study; November operations discussion. No real KPI results are available in these discussions.
