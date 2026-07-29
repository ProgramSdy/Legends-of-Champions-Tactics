# Codex Project Rules

These are stable working rules for Codex. Read this file before starting any
project task.

## Five-Agent Collaboration — Mandatory Golden Rule

Every project task must activate and use all five configured Codex agents:

1. `project-manager`
2. `ui-developer`
3. `game-engine-developer`
4. `test-automator`
5. `reviewer`

Before conducting each task, read `docs/Codex/Agent_Roles.md` and the current
definitions for all five agents under `.codex/agents/`.

The `project-manager` must coordinate the work and explicitly assign a scoped
responsibility to every agent before implementation begins. Participation is
mandatory for all five agents, but its depth must be proportional to the task.
An agent whose area requires no implementation changes must still perform a
bounded impact assessment and report a documented no-change conclusion. It
must not invent work, expand scope, or make unnecessary edits merely to
participate.

The implementation specialists work within their ownership boundaries. The
`test-automator` validates the integrated result. The `reviewer` performs an
independent final review after validation. The `project-manager` resolves
findings, consolidates the outcome, updates documentation, and records
completion.

If concurrency or tool limits prevent simultaneous activation, the agents must
work in coordinated waves. All five must still report an outcome before the
task can be marked complete.

Codex must never silently complete a project task through one agent or with
fewer than all five configured agents.

## Before Editing

1. Read `docs/README.md`.
2. Read `docs/onboarding/ONBOARDING_SUMMARY.md`.
3. Read `docs/Codex/Project_Rules.md`.
4. Read `docs/Codex/Agent_Roles.md` and all five definitions in
   `.codex/agents/`.
5. Read `docs/Codex/Current_Task.md`.
6. Have the `project-manager` assign explicit responsibilities to all five
   agents.
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
- each agent's contribution or documented no-change conclusion;
- a summary and files changed;
- validation performed and its actual results;
- reviewer findings and disposition;
- unresolved issues and recommended follow-up work.
