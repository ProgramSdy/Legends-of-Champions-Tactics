# Agent Routing Audit — 2026-09-11

## Finding

The project workflow has **not** intentionally changed to single-agent work.
`Agent_Roles.md` and `Project_Rules.md` both retain proportional assignment:
official `Current_Task.md` work normally uses all five configured roles, while
narrower work must document a project-manager rationale for each omitted role.

## Evidence

- The five configured role definitions exist and are readable:
  `project-manager`, `ui-developer`, `game-engine-developer`,
  `test-automator`, and `reviewer`.
- Earlier completion records consistently contain an **Agent Selection and
  Contributions** section, including rationales for narrower frontend-only
  tasks and all-five treatment for cross-boundary work.
- Recent UI-025 and COMBAT-008 completion records lacked that selection and
  contribution evidence. COMBAT-008's task document listed all five roles, but
  the work began without a recorded project-manager assessment or confirmed
  role dispatch. This is execution/documentation drift, not an intentional
  classification that those official tasks were narrow.
- At audit time, the live sub-agent slots report a service usage-limit error.
  That is a current dispatch blocker, but it does not remove the need to
  perform and document the selection step before work begins.

## Correction

The workflow now explicitly distinguishes a listed role from a selected and
dispatched role. Official tasks must record risk/complexity, concrete ownership,
and omitted-role rationales before implementation. If a selected agent is
unavailable, the task must record the blocker and use later coordinated waves
or obtain owner approval for a fallback. Completion records must not credit a
role that was not actually dispatched.

## Going Forward

Use all five roles by default for official cross-boundary tasks and bug fixes.
Use a smaller team only for genuinely narrow work, with the reason documented
before the first edit. This restores the existing proportional policy without
forcing artificial no-change reports.
