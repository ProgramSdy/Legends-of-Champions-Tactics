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
7. Have the `project-manager` announce explicit assignments for all five agents.
8. Review relevant GDD, Technical, onboarding, and web-ui documents and inspect
   the affected repository implementation before making changes.
9. Check `Codex/Backlog.md` only when the project owner has authorised it.

## Mandatory Five-Agent Cooperation

Every project task must be conducted through cooperation among all five
configured Codex agents:

- `project-manager`
- `ui-developer`
- `game-engine-developer`
- `test-automator`
- `reviewer`

The `project-manager` coordinates every task. All five agents must participate,
although their depth of work is proportional to the task. An agent with no
implementation ownership must still perform a bounded impact review and report
that no changes are required. This rule does not authorise unnecessary work or
scope expansion.

Read `Codex/Agent_Roles.md` before every task. Codex must not silently complete
a project task through a single agent or with fewer than all five configured
agents.

## Folder Guide

- `onboarding/` — Existing project overview, architecture analysis, open questions, and onboarding material.
- `GDD/` — Authoritative gameplay and game-design documents.
- `Technical/` — Authoritative technical architecture and system-design documents.
- `web-ui/` — Web UI architecture, contracts, screenshots, reviews, flows, and visual standards.
- `Codex/` — Stable project rules, mandatory agent roles, the current task,
  backlog, completed work, and analysis.
- `Meeting_Notes/` — Dated discussions, decisions, and review notes.

## Documentation Rules

- Preserve existing documents unless a task explicitly asks to replace or retire them.
- Analysis records an observation at a point in time; authoritative documents record the current agreed design.
- Update the relevant documentation when implementation changes behaviour, architecture, data contracts, or UI flows.
- Use relative repository paths in technical notes.
- Record unresolved questions clearly rather than making silent assumptions.
