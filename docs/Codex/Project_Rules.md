# Codex Project Rules

These are stable working rules for Codex. Read this file before starting any implementation task.

## Before Editing

1. Read `docs/README.md`.
2. Read the relevant onboarding, GDD, Technical, and web-ui documents.
3. Inspect the actual repository files related to the task.
4. State material assumptions in the task completion report.

## Implementation Rules

- Preserve existing working behaviour unless the active task explicitly changes it.
- Do not perform unnecessary architectural rewrites.
- Respect established ownership boundaries between systems.
- Avoid duplicating authoritative logic in another layer.
- Keep changes focused on the active task.
- Follow existing project conventions unless a documented decision changes them.
- Never commit credentials, secrets, generated private data, or machine-specific paths.
- Mark temporary shortcuts and technical debt clearly.

## Validation Rules

- Run the relevant automated tests.
- Run type checks, linting, builds, or project validation where applicable.
- Report commands run and their results honestly.
- Do not claim validation that was not performed.
- Record blockers and unresolved risks.

## Documentation Rules

- Update documentation when behaviour, architecture, data contracts, or UI flow changes.
- Preserve historical analysis unless explicitly asked to archive it.
- Put stable truth in GDD, Technical, or web-ui documents.
- Put temporary investigations and point-in-time analysis in `Codex/Analysis/`.

## Completion Rules

When a task is complete, update `Completed.md` with the date, task title, summary, files changed, validation performed, and unresolved follow-up work.
