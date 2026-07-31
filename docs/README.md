# Legends of Champions Tactics — Documentation Hub

This folder is the shared project documentation space for the project owner, ChatGPT, and Codex.

## Start Here

Codex should begin each work session in this order:

1. Confirm the repository root.
2. Read this documentation hub.
3. Read `onboarding/ONBOARDING_SUMMARY.md`.
4. Read `Codex/Project_Rules.md`.
5. Read `Codex/Agent_Roles.md` and all five configured definitions under
   `.codex/agents/`.
6. Read `Codex/Current_Task.md`.
7. Have the `project-manager` assess the task's type, complexity, affected
   systems, and risk, then announce the selected agent assignment(s).
8. Review relevant GDD, Technical, onboarding, and web-ui documents and inspect
   the affected repository implementation before making changes.
9. Check `Codex/Backlog.md` only when the project owner has authorised it.

## Proportional Agent Cooperation

Project work uses the five configured Codex roles:

- `project-manager`
- `ui-developer`
- `game-engine-developer`
- `test-automator`
- `reviewer`

The `project-manager` assesses every task and assigns one or more relevant
agents according to the task type, affected ownership boundaries, complexity,
and risk. Simple, low-risk work may use only the project manager and the
directly relevant specialist. More complex or cross-system work should involve
more agents.

An official task assigned through `Codex/Current_Task.md` will normally involve
all five agents, especially a bug-fix task. The project manager may select fewer
only when the documented scope and risk justify it, and must record that
rationale. Agents must not be activated merely to manufacture work or
unnecessary no-change reports.

Read `Codex/Agent_Roles.md` before every task. Codex must follow and report the
project manager's explicit selection rather than silently choosing or omitting
roles.

## Folder Guide

- `onboarding/` — Existing project overview, architecture analysis, open questions, and onboarding material.
- `GDD/` — Authoritative gameplay and game-design documents.
- `Technical/` — Authoritative technical architecture and system-design documents.
- `web-ui/` — Web UI architecture, contracts, screenshots, reviews, flows, and visual standards.
- `Codex/` — Stable project rules, configured agent roles, the current task,
  backlog, completed work, and analysis.
- `Meeting_Notes/` — Dated discussions, decisions, and review notes.

## Documentation Rules

- Preserve existing documents unless a task explicitly asks to replace or retire them.
- Analysis records an observation at a point in time; authoritative documents record the current agreed design.
- Update the relevant documentation when implementation changes behaviour, architecture, data contracts, or UI flows.
- Use relative repository paths in technical notes.
- Record unresolved questions clearly rather than making silent assumptions.
