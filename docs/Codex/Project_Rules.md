# Codex Project Rules

These are stable working rules for Codex. Read this file before starting any
project task.

## Agent Collaboration — Proportional Golden Rule

Project work uses these five configured Codex roles:

1. `project-manager`
2. `ui-developer`
3. `game-engine-developer`
4. `test-automator`
5. `reviewer`

Before conducting each task, read `docs/Codex/Agent_Roles.md` and the current
definitions for the roles selected under `.codex/agents/`. Consult other role
definitions only when task boundaries make them relevant.

The Core lead briefly assesses the request's type, affected systems, and risk,
then assigns only the roles needed. Dispatch the `project-manager` when
sequencing or coordination across workstreams needs a separate owner; a simple
task does not require a project-manager subagent. Agent involvement must be
proportional: simple and low-risk work needs fewer roles; complex, high-risk,
or cross-system work may need broader cooperation.

An official task assigned through `docs/Codex/Current_Task.md` does not by
itself require all five agents. Select roles by the actual work and risk, even
for bug fixes. A simple appearance change can use the frontend engineer alone
or with a brief reviewer check. State selected ownership and a short reason
for omitted roles; non-participating agents do not produce reports.

Selected implementation specialists work within their ownership boundaries.
When selected, the `test-automator` validates the integrated result and the
`reviewer` performs an independent review. Core resolves
findings, consolidates the outcome, updates documentation, and records
completion in proportion to the task.

If concurrency or tool limits prevent simultaneous activation, selected agents
may work in coordinated waves.

Codex must never silently bypass the role-selection step or omit a role that
the documented assignment selected.

A listed role counts as selected only after it has concrete ownership and is
actually dispatched. An unavailable agent must be recorded as a blocker, not
represented as having participated. Do not begin implementation on an official
task from a generic assignment list alone: record Core's
risk/complexity assessment, selected roles, and omitted-role rationales first.
If the selected team cannot run because of concurrency or service limits, use
documented coordinated waves or obtain owner approval for a temporary fallback.

## Before Editing

1. Read `docs/README.md`.
2. Read `docs/onboarding/ONBOARDING_SUMMARY.md`.
3. Read `docs/Codex/Project_Rules.md`.
4. Read `docs/Codex/Agent_Roles.md` and the selected role definitions in
   `.codex/agents/`.
5. Read `docs/Codex/Current_Task.md`.
6. Have Core assess complexity and risk, then assign explicit responsibilities
   to only the relevant agent or agents.
7. Read the relevant onboarding, GDD, Technical, and web-ui documents.
8. Inspect the actual repository files related to the task.
9. State material assumptions in the task completion report.

## Implementation Rules

- Preserve existing working behaviour unless the active task explicitly
  changes it.
- Do not perform unnecessary architectural rewrites.
- Respect established ownership boundaries between systems.
- Avoid duplicating authoritative logic in another layer.
- Keep changes focused on the active task.
- Follow existing project conventions unless a documented decision changes
  them.
- Never commit credentials, secrets, generated private data, or
  machine-specific paths.
- Mark temporary shortcuts and technical debt clearly.

## Validation Rules

- Use the smallest check that can establish the changed behaviour. For a
  low-risk appearance or documentation edit, a focused visual/diff check may
  be enough; do not add tests that only mirror the edit.
- Add or run focused automated tests when behaviour, contracts, or regression
  risk warrants them. Run broader suites, type checks, linting, or builds only
  when the affected boundary or a concrete failure warrants that extra scope.
- Do not repeat passing checks or extend a manual walkthrough without a
  specific unresolved risk. If an unrelated baseline failure blocks a broad
  suite, identify it once, report it, and stop retesting it for this task.
- Keep review proportional: a small change may need only a brief targeted
  inspection, while high-risk or cross-system work may need independent review.
- Report commands run and their results honestly.
- Do not claim validation that was not performed.
- Record blockers and unresolved risks.

## Time and Communication Discipline

- Work toward the requested outcome with the smallest effective team and
  shortest useful validation path. Do not turn a simple UI adjustment into a
  multi-agent or multi-hour audit.
- Core reports to the Documentation Planner once when the task is finished, or
  sooner only for a real blocker or owner decision. Do not send routine agent
  progress, test-by-test updates, or repeated status messages across chats.
- The planner sends one concise handoff and does not repeatedly poll or relay
  Core's internal progress. An owner-requested status check is an exception.
- When a check reveals a specific defect, fix it and verify that defect. Do
  not expand the task into unrelated cleanup or additional investigations.

## New Hero and Status Integration Gate

Before exposing a hero through the live roster, Codex must inventory every
player-visible status and combat outcome that the hero can apply, refresh,
remove, expire, or prevent. The implementation gate requires synchronized
evidence that:

- the engine has one authoritative lifecycle, source, duration, and cleanup
  path for each visible status/outcome;
- the adapter serializes its stable status IDs and any typed outcome events with
  authoritative source/target data, without inferring state from snapshots;
- frontend status metadata, shared icons/tooltips, and target-bound effects
  consume only those supplied identifiers and typed events; and
- deterministic backend/frontend regression tests cover application, refresh,
  removal or expiry, and relevant positive and false-positive outcome paths.

Do not expose the hero until the status/outcome inventory and this
cross-boundary validation are complete. Whitelist expansion in one layer alone
is not sufficient.

## Documentation Rules

- Update documentation when behaviour, architecture, data contracts, or UI
  flow changes.
- Preserve historical analysis unless explicitly asked to archive it.
- Put stable truth in GDD, Technical, or web-ui documents.
- Put temporary investigations and point-in-time analysis in
  `docs/Codex/Analysis/`.

### UI Review Ownership and Workflow

- `docs/web-ui/screenshots_debug/UI_Review_Human.md` is controlled exclusively
  by the project owner.
- Codex and ChatGPT must never edit, rewrite, reformat, rename, replace, or
  delete `UI_Review_Human.md`.
- Annotated screenshots in `docs/web-ui/screenshots_debug/` and the matching
  numbered notes in `UI_Review_Human.md` are the owner's source input for UI
  review.
- ChatGPT converts the owner's review into authoritative implementation
  documentation, normally including:
  - `docs/web-ui/UI_Review.md`
  - `docs/Codex/Current_Task.md`
  - `docs/Codex/Project_Rules.md` only when a stable workflow rule must change
- Codex implements only from the generated authoritative task documents and
  may use the owner file and screenshots as read-only evidence.
- Codex must not mark an owner-reported UI issue complete merely because code
  changed; it must validate against the documented acceptance criteria and
  provide evidence.
- When implementation is complete, Codex updates
  `docs/Codex/Completed.md` and records unresolved owner-review items.

## Completion Rules

When a task is complete, update `docs/Codex/Completed.md` with:

- the completion date and task title;
- each participating agent's contribution and a brief role-selection rationale;
- a summary and files changed;
- validation performed and its actual results;
- reviewer findings and disposition when the reviewer participated;
- unresolved issues and recommended follow-up work.
