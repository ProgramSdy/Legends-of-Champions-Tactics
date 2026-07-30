# UI Review 002


## Date


2026-07-29


## Source


Owner requirements in `docs/web-ui/screenshots_debug/UI_Review_Human.md`. That file is owner-controlled and read-only.


## Title


Team Builder, Expanded Hero Roster, and Live 2v2/3v3 Battles


## Findings


1. The current flow exposes only `Warrior_Weapon_Master` and `Rogue_Comprehensiveness`.
2. There is no Team Builder before battle.
3. The live Python-backed path is limited to 1v1.
4. There is no explicit finished-battle return path to team setup.


## Approved Roster


- `Priest_Comprehensiveness`
- `Priest_Discipline`
- `Paladin_Retribution`
- `Paladin_Protection`
- `Mage_Comprehensiveness`
- `Warrior_Defence`
- `Warrior_Weapon_Master`
- `Rogue_Comprehensiveness`


## Requested Changes


- Add Team Builder as the normal entry point before battle.
- Let the player choose `1v1`, `2v2`, or `3v3`.
- Require complete player and enemy teams matching the selected battle size.
- Keep all player-team heroes player-controlled.
- Provide enemy composition modes: random or player specified.
- Provide enemy control modes: computer control using existing Python-engine logic, or player control.
- Carry battle size, teams, and control modes through typed frontend/provider/API contracts.
- Extend the live adapter/session path to support 2v2 and 3v3 using the existing Python engine as gameplay authority.
- Render all selected combatants, legal actions, targets, HP, statuses, events, turns, and results correctly.
- On battle completion, display a popup or modal with a button returning to Team Builder.
- Reset transient battle/session/presentation state on return.
- Preserve all verified UI-001 behaviour.


## Acceptance Criteria


- All eight approved heroes are selectable and work in valid live sessions.
- Team Builder validates and launches 1v1, 2v2, and 3v3 configurations.
- Incomplete or invalid teams cannot start.
- Random enemy selection produces a valid complete team.
- Player-specified enemy selection fills every enemy slot.
- Player-team heroes remain player-controlled.
- Enemy control can be switched between Python-engine computer control and player control.
- Live 1v1, 2v2, and 3v3 use the engine-authoritative adapter path.
- Human turns expose correct legal actions and targeting.
- Computer-controlled turns progress without player input using existing engine logic.
- The battle screen correctly renders all combatants and authoritative battle state for all three sizes.
- Finished battle shows a clear return action.
- Return to Team Builder leaves no stale events, selections, timers, commands, or session state.
- Existing authoritative Battle Log, stable skill-card sizing, HP/status display, and status-tooltip behaviour remain intact.
- Automated tests cover roster availability, Team Builder validation, random/specified enemies, both control modes, live 2v2/3v3, turn progression, computer turns, and return/reset.
- Frontend tests, type-check, lint, build, Python tests, adapter/API tests, and live browser validation pass.
- `UI_Review_Human.md` has no diff.


## Status


Implemented and independently reviewed on 2026-07-29.


## Completion Evidence


- All eight approved definitions are returned by `GET /api/v1/heroes` and
  construct valid live sessions.
- Team Builder launches validated 1v1, 2v2, and 3v3 configurations with random
  or specified enemies and computer or player enemy control.
- Python remains authoritative for composition randomness, legal actions,
  targeting, computer turns, mutations, ordering, and outcomes.
- Finished battles show a keyboard-contained outcome dialog and return to a
  clean Team Builder; relaunch creates a fresh provider and session.
- Frontend validation passed with 57 tests, TypeScript, ESLint, and production
  build. Python validation passed with 59 tests, including authoritative
  incapacitated-turn progression and forced Scoff targeting for player and
  computer actors.
- Browser validation covered all three required live configurations,
  player-controlled enemy action, computer-turn draining, completion/return,
  relaunch, 1280×720 trio layout, log/skill stability, and status hover/focus.
- Independent review found no blocking implementation issue. Its documentation
  finding was resolved through the authoritative UI-002 updates.
