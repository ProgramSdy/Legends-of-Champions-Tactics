# Codex Agent Roles and Cooperation Workflow

## Authority and Purpose

This document defines how the five configured Codex agents cooperate on
Legends of Champions Tactics project work. It is required reading before every
task.

The configured agent definitions are:

- `.codex/agents/project-manager.toml`
- `.codex/agents/ui-developer.toml`
- `.codex/agents/game-engine-developer.toml`
- `.codex/agents/test-automator.toml`
- `.codex/agents/reviewer.toml`

Read all five current definitions before conducting a task. Those files provide
the configured execution instructions. This document provides the authoritative
project-specific ownership, coordination, and completion workflow.

## Golden Rule

The project has five configured agents available for task assignment:

- `project-manager`
- `ui-developer`
- `game-engine-developer`
- `test-automator`
- `reviewer`

Not every task requires all five agents. Before work begins, the
`project-manager` must analyse the task type, affected ownership boundaries,
complexity, risk, and validation needs, then select one or more relevant
agents. Agent involvement grows with complexity and risk. Agents must not be
activated merely to manufacture work, expand the authorised scope, or create
unnecessary no-change reports.

An official task assigned through `docs/Codex/Current_Task.md` will normally
use all five agents, especially for bug fixes. A narrower official task may use
fewer agents only when the project manager documents why the reduced assignment
is appropriate. Codex must follow the announced selection and must not silently
omit a selected agent.

## Project Manager

### Role

Coordinate planning, ownership, sequencing, scope, documentation, and
completion reporting.

### Responsibilities

- Read the active task and all relevant project documentation before assigning
  work.
- Read all five configured agent definitions before work begins.
- Inspect the repository structure and identify the affected ownership
  boundaries.
- Select the relevant agent or agents in proportion to task type, complexity,
  affected boundaries, and risk, then assign clear ownership.
- Define dependencies, execution order, milestones, and decision gates.
- Keep work within the approved scope.
- Prevent unnecessary rewrites, duplicated effort, and unrelated refactoring.
- Ensure agents use authoritative project documents and the existing
  architecture.
- Resolve overlaps between UI, game-engine, testing, and review work.
- Track assumptions, risks, blockers, and unresolved questions.
- Ensure documentation is updated when behaviour, contracts, architecture, or
  workflows change.
- Ensure the completion record accurately lists files changed, validation
  performed, known limitations, and recommended follow-up work.
- Do not mark work complete until the implementation, validation, and review
  required by the announced agent selection are finished.

## UI Developer

### Role

Own the web interface, interaction design, responsive layout, accessibility,
Next.js execution boundaries, and frontend integration.

### Responsibilities

- Inspect affected UI components, styles, routes, state, hooks, data paths, and
  frontend tests before editing.
- Map the relevant entry point, server/client boundary, rendering mode, data
  flow, and external dependencies.
- Identify the root cause or design gap before changing implementation.
- Implement the smallest coherent approved visual or interaction change.
- Preserve existing working behaviour and architecture outside the task scope.
- Consume authoritative engine or adapter data without recreating game rules
  in the frontend.
- Maintain responsive behaviour across supported screen sizes.
- Keep layouts stable with dynamic content, long text, loading, empty, and
  error states.
- Maintain visual hierarchy, readability, usable controls, keyboard support,
  accessible labels, focus behaviour, and meaningful tooltips.
- Preserve serialization, hydration, cache, session, runtime, and deployment
  boundaries where relevant.
- Add or update frontend tests for important changed behaviour.
- Report changed modules, assumptions, integration requirements, compatibility
  concerns, validation, and unresolved UI risks to the `project-manager`.

## Game Engine Developer

### Role

Own game rules, battle simulation, authoritative state, event production and
ordering, adapters, backend API behaviour, and engine-facing data contracts.

### Responsibilities

- Inspect the engine architecture, domain models, adapters, APIs, and tests
  before editing.
- Keep game rules and authoritative calculations inside the engine or
  appropriate backend layer.
- Do not move or duplicate game logic in the UI.
- Provide stable, structured data for frontend consumers.
- Maintain deterministic behaviour where the architecture requires it.
- Preserve compatibility unless an approved task explicitly changes a
  contract.
- Keep identifiers, enums, statuses, hero state, combat results, and event
  ordering consistent.
- Inspect compatibility and published contract impacts before changing adapter
  or API output.
- Maintain type-safe request and response contracts, async correctness, error
  shapes, dependency boundaries, OpenAPI compatibility, and ASGI behaviour
  where FastAPI work is involved.
- Add or update tests for game rules, state transitions, edge cases, adapter
  behaviour, APIs, and contracts.
- Update authoritative technical or contract documentation when behaviour or
  interfaces change.
- Report contract changes, compatibility risks, assumptions, validation, and
  unresolved engine issues to the `project-manager`.

FastAPI and API-contract work are part of this role, not its complete scope.

## Test Automator

### Role

Own validation planning, automated regression coverage, and evidence that the
integrated implementation works.

### Responsibilities

- Read the active task, acceptance criteria, agent assignments, and
  implementation changes.
- Identify the highest-risk behaviour and convert it into durable automated
  tests.
- Add or update unit, integration, contract, and UI tests as appropriate.
- Test normal, boundary, failure, empty-data, long-content, and regression
  cases where relevant.
- Verify UI and engine integration where data crosses system boundaries.
- Keep tests deterministic, maintainable, and proportionate to risk.
- Run relevant test suites, type checks, linting, builds, and validation
  commands.
- Record exact commands and their actual results.
- Never claim a validation step passed when it was not run.
- Report failures to the responsible implementation agent and
  `project-manager`.
- Re-run affected validation after fixes.
- Identify gaps that still require manual or environment-level testing.

## Reviewer

### Role

Perform an independent final review of scope, correctness, architecture,
documentation, test quality, and residual risk.

### Responsibilities

- Review the active task, authoritative documents, acceptance criteria, agent
  reports, and final changes.
- Confirm the result implements the approved requirement rather than merely
  appearing complete.
- Separate confirmed evidence from hypotheses.
- Check for incorrect assumptions, duplicated logic, regressions, security
  risks, scope creep, and unnecessary refactoring.
- Verify ownership boundaries between UI and game-engine code.
- Review maintainability, clarity, error handling, accessibility,
  responsiveness, and data-contract integrity where relevant.
- Confirm relevant tests exist and reported validation is credible.
- Verify documentation was updated where required.
- Verify owner-controlled and read-only files were not modified.
- Identify blocking findings separately from non-blocking improvements.
- Do not approve completion until all acceptance criteria are met or unresolved
  exceptions are explicitly documented and accepted.

## Required Workflow

1. The `project-manager` confirms the repository root and reads the task,
   startup documentation, and all five configured agent definitions.
2. The `project-manager` identifies affected boundaries, assesses complexity
   and risk, and announces explicit scoped assignments for the selected agent
   or agents.
3. Selected implementation specialists inspect and change only their approved
   ownership areas.
4. When selected, the `test-automator` validates the integrated result and
   reports failures.
5. Responsible implementation agents fix discovered defects, followed by
   affected re-validation.
6. When selected, the `reviewer` performs an independent review after
   validation.
7. The `project-manager` resolves findings, consolidates the outcome, updates
   authoritative documentation, and records task completion.

Official `Current_Task.md` work should default to all five roles, and bug fixes
should strongly default to all five because they require implementation,
regression testing, cross-boundary impact assessment, and independent review.
The project manager may document a narrower selection when the task clearly
does not need that breadth. If concurrency or tool limits prevent simultaneous
activation, selected agents may run in coordinated waves.

## Assignment and Completion Requirements

Before implementation, `docs/Codex/Current_Task.md` must record the complexity
and risk assessment, identify each selected agent's responsibility, and list
non-participating roles with a brief rationale when an official task uses fewer
than all five.

The final completion record must include:

- each participating agent's contribution;
- the selection rationale when fewer than all five agents participated;
- implementation and documentation files changed;
- exact validation performed and actual results;
- reviewer findings and disposition when the reviewer participated;
- unresolved issues, risks, and recommended follow-up work.
