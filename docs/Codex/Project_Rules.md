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
definitions for all five agents under `.codex/agents/`.

The `project-manager` coordinates every task. Before work begins, it must assess
the request's type, complexity, affected systems, ownership boundaries, and
risk, then explicitly assign one or more relevant configured agents. Agent
involvement must be proportional: simple and low-risk work needs fewer roles;
complex, high-risk, or cross-system work needs broader cooperation.

An official task assigned through `docs/Codex/Current_Task.md` will normally
involve all five configured agents, especially when it is a bug fix. The
project manager may use fewer agents when the official task is genuinely
narrow or low risk, but the assignment must state why each omitted role is not
needed. Non-participating agents do not need to produce artificial no-change
reports.

Selected implementation specialists work within their ownership boundaries.
When selected, the `test-automator` validates the integrated result and the
`reviewer` performs an independent review. The `project-manager` resolves
findings, consolidates the outcome, updates documentation, and records
completion in proportion to the task.

If concurrency or tool limits prevent simultaneous activation, selected agents
may work in coordinated waves.

Codex must never silently bypass the project manager's agent-selection step or
omit a role that the documented assignment selected.

## Before Editing

1. Read `docs/README.md`.
2. Read `docs/onboarding/ONBOARDING_SUMMARY.md`.
3. Read `docs/Codex/Project_Rules.md`.
4. Read `docs/Codex/Agent_Roles.md` and all five definitions in
   `.codex/agents/`.
5. Read `docs/Codex/Current_Task.md`.
6. Have the `project-manager` assess complexity and risk, then assign explicit
   responsibilities to the relevant agent or agents. For an official task,
   record any justified departure from the normal five-agent involvement.
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

- Run the relevant automated tests.
- Run type checks, linting, builds, or project validation where applicable.
- Report commands run and their results honestly.
- Do not claim validation that was not performed.
- Record blockers and unresolved risks.

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
- each participating agent's contribution and the project manager's selection
  rationale where fewer than all five agents were used;
- a summary and files changed;
- validation performed and its actual results;
- reviewer findings and disposition when the reviewer participated;
- unresolved issues and recommended follow-up work.
