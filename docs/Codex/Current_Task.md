# Current Task

## Status

In Progress

---

## Task ID

UI-017

## Title

Activate Warrior's Barrack and Its Three-Battle Structured Training Sequence

## Objective

Activate Warrior's Barrack as the first structured Stage Map training location
and deliver its temporary, data-driven three-battle sequence while preserving
the existing Arena and introducing no player-data, save, database, or
progression implementation.

## Background

The current Stage Map has one enabled location, Arena, which routes to
`/game?stage=arena`. `stage-config.ts` is the current presentation owner for
stage IDs, display names, enabled state, destinations, and percentage-based map
geometry. The existing map artwork already contains the left-side red-banner
fortress that represents Warrior's Barrack; activate it with a percentage-based
hotspot on the supplied map rather than changing the artwork or redesigning the
map.

The present Team Builder is Arena configuration mode: it fetches the live
ten-hero roster, allows 1v1/2v2/3v3 and enemy configuration, then sends the
existing `BattleCreateConfiguration` to the Python adapter. `BattleExperience`
owns local provider creation and return from the completion dialog. The adapter
already accepts all needed stable IDs and battle sizes, so no backend rule,
adapter schema, or API endpoint change is required for this task.

UI-014 established the exact approved roster IDs below. Do not create aliases
or duplicate definitions:

| Use | Stable definition ID | Faculty · Specialization |
|---|---|---|
| Barrack player roster | `hero.warrior.weapon_master` | Warrior · Weapon Master |
| Barrack player roster | `hero.mage.comprehensiveness` | Mage · Comprehensiveness |
| Barrack player roster | `hero.priest.comprehensiveness` | Priest · Comprehensiveness |
| Barrack player roster | `hero.rogue.comprehensiveness` | Rogue · Comprehensiveness |
| Predefined enemy | `hero.warrior.defence` | Warrior · Defence |
| Predefined enemy | `hero.warrior.berserker` | Warrior · Berserker |

`Player_Data_and_Save_System.md` defines future persistent profiles, stage
progression, autosave, recovery, and unlocks. That system is intentionally
paused. This task may keep temporary in-memory stage-session state only; a
refresh/restart may lose it and must not be represented as implemented recovery.

## Authoritative References

- `docs/README.md` — documentation hierarchy and workflow.
- `docs/Codex/Project_Rules.md` and `docs/Codex/Agent_Roles.md` — project
  boundaries, agent selection, validation, and completion requirements.
- `docs/Codex/Completed.md` — UI-012 Stage Map, UI-013–UI-015 Team Builder,
  UI-014 ten-hero roster, and UI-016 status work already completed.
- `docs/web-ui/Screen_Flow.md` — current `/` → `/stages` → `/game` lifecycle
  and agreed-but-unimplemented persistent-profile design.
- `docs/web-ui/WEB_UI_ARCHITECTURE.md` and `docs/web-ui/Style_Guide.md` — stage
  ownership, presentation boundaries, accessibility, and visual standards.
- `docs/GDD/Game_Design_Document.md`, `docs/GDD/Combat_System.md`, and
  `docs/GDD/Hero_System.md` — Python combat authority, battle formats, and
  stable hero roster IDs.
- `docs/Technical/Player_Data_and_Save_System.md` — future persistence
  boundary; reference only, do not implement.

## Current-System Investigation

- `StageSelectionScreen.tsx` derives enabled controls from `STAGE_DEFINITIONS`
  and routes through `?stage=<stageId>`. Its map parent uses the intrinsic
  1672 × 941 source coordinate system, so the Barrack hotspot must use map
  percentages, not viewport pixels.
- `GamePage` resolves an enabled stage ID and supplies it to
  `BattleExperience`; direct/invalid visits currently fall back to Arena.
- `TeamBuilder.tsx` owns local team choice and sends only the existing
  battle-size, ordered player/enemy teams, enemy mode/control, and optional
  seed configuration. It already uses shared avatar/fallback rendering and
  supports fixed visual slots.
- `BattleExperience.tsx` creates one live provider from that configuration and
  currently returns from every ended battle to Team Builder. It is the narrow
  point to introduce temporary structured-stage progression and outcome-aware
  completion routing.
- `BattleScreen.tsx` has the authoritative snapshot outcome in its completion
  dialog. It must supply the outcome to the owning lifecycle rather than make
  Team Builder or React infer victory from UI text.
- `battle_api/adapter.py` and `battle_api/models.py` already accept each
  required hero ID in 1v1, 2v2, and 3v3 and support specified enemy teams.
  Existing Python engine/gameplay rules must remain unchanged.

## Stage Definition

1. Activate the existing `warriors-barrack` stage definition while retaining
   Arena as enabled and every other named location inactive.
2. Give it the existing `/game` destination and a responsive percentage-based
   hotspot positioned over the left-side red-banner Warrior's Barrack landmark
   in `valley_of_champions.png`. Tune only through the existing debug-hotspot
   mechanism and capture browser evidence at representative viewports.
3. Add a small reusable structured-stage data model rather than embedding a
   Barrack-only conditional throughout components. It must express, at minimum:
   - stage ID/display name;
   - allowed player definition IDs; and
   - ordered battle definitions with stable battle ID/display order, fixed
     battle size, and fixed enemy definition IDs.
4. Keep this configuration presentation/session data only. Do not model
   completion persistence, unlocks, profile ownership, database records, or a
   campaign framework beyond what Warrior's Barrack needs.

## Battle Definitions

Warrior's Barrack uses this exact ordered sequence:

| Order | Stable battle ID | Format | Fixed enemy definition IDs |
|---|---|---|---|
| Battle 1 | `warriors-barrack.battle-1` | 2v2 | `hero.warrior.defence`, `hero.priest.comprehensiveness` |
| Battle 2 | `warriors-barrack.battle-2` | 1v1 | `hero.warrior.weapon_master` |
| Battle 3 | `warriors-barrack.battle-3` | 3v3 | `hero.warrior.defence`, `hero.warrior.berserker`, `hero.priest.comprehensiveness` |

For all three, the selectable player roster is exactly:

- `hero.warrior.weapon_master`
- `hero.mage.comprehensiveness`
- `hero.priest.comprehensiveness`
- `hero.rogue.comprehensiveness`

Filter the adapter-provided roster by these IDs for structured mode. Validate
that every configured ID is present before exposing the builder; show a clear,
retryable configuration/roster error rather than silently substituting a hero.
The player may select required heroes from this list using the existing Matrix
and fallback artwork, including duplicates if the existing battle contract
continues to permit them. Do not globally remove the other six heroes or alter
Arena's complete roster.

## Team Builder Requirements

1. Reuse Team Builder in two explicit modes:
   - **Arena configuration mode:** preserve all existing controls, roster,
     payloads, and behaviour exactly.
   - **Structured Stage Battle mode:** render the configured Warrior's Barrack
     battle and allow only player-team selection.
2. In structured mode, clearly show:
   - `Warrior's Barrack`;
   - `Battle 1`, `Battle 2`, or `Battle 3` and the sequence context;
   - fixed 2v2, 1v1, or 3v3 format; and
   - the predefined enemy team using existing avatar/fallback cards and
     profession labels.
3. The structured enemy is visible but immutable. Do not render editable enemy
   selects, Random/Choose team controls, enemy-control choices, or an editable
   battle-size control for a predefined battle. Do not expose an Arena-style
   configurable enemy through keyboard or assistive-technology-only controls.
4. Build the existing compatible creation payload in structured mode with the
   fixed battle size, `enemyCompositionMode: "specified"`, exact fixed
   `enemyTeam`, and existing computer enemy control. Do not add a stage or
   progression field to `BattleCreateConfiguration` or the Python API.
5. Preserve Team Builder accessibility: clear headings, visible focus,
   keyboard assignment of player slots/Matrix cards, accessible fixed-enemy
   summary, and standard image fallback. Keep the current stage preview and
   Back to Stage Map navigation useful; leaving structured mode via Stage Map
   ends only its temporary in-memory session.

## Progression Requirements

1. Selecting Warrior's Barrack starts an in-memory structured-stage session at
   Battle 1 preparation. It must not rely on browser history as the source of
   truth and must not persist to storage.
2. On an authoritative friendly victory:
   - Battle 1 → show Battle 2 Team Builder;
   - Battle 2 → show Battle 3 Team Builder;
   - Battle 3 → navigate to `/stages` and clear the temporary sequence state.
3. On defeat, draw, or round-limit outcome, keep the current stage battle and
   provide the smallest clear temporary action: **Retry Battle**. Retrying
   discards only the current live provider and returns to that battle's
   Team Builder with the fixed stage definition; it does not advance, reset
   earlier completed battles, award/revoke rewards, or invent penalties.
4. Completion actions must consume the actual authoritative outcome supplied by
   `BattleScreen`/provider state. Never progress based on a log message, UI
   label, or assumed winner.
5. A page refresh, browser restart, or route reload may restart or lose the
   temporary sequence. Surface no Resume/Abandon/Persistence claim; the future
   Player Data and Save System is the planned solution.

## Architecture Requirements

- Keep stage/battle definitions independent of the Python battle engine and
  reuse the existing creation contract. The engine is authoritative for live
  battle results, skill rules, AI, random values, and all combat state.
- Keep the temporary sequence orchestrator at the existing frontend lifecycle
  boundary (`BattleExperience` or a narrowly extracted client-side stage-session
  owner), not inside `StageSelectionScreen`, the server route, or global
  persistence.
- Make battle completion outcome-aware through a small typed callback/interface
  improvement at the existing BattleScreen → BattleExperience boundary.
- Avoid hard-coded screen-specific battle arrays or special cases that would
  require duplicating Team Builder to add a future structured location. Do not
  over-engineer a general campaign, routing framework, or persistence layer.
- Do not alter public battle API request/response schemas, Python models,
  adapter behaviour, combat balance, hero skills, or asset pixels.

## Out of Scope

- Player Data / Save System, SQLite, player profiles, New Game/Continue Game,
  autosave, Resume/Abandon Battle, persistence, hero ownership/unlocks, stage
  completion storage, rewards, and database schemas.
- PvP, disconnect/forfeit behaviour, currencies, experience, inventory, boss
  battles, campaign framework, or activation/change of other Stage Map
  locations.
- Combat balance, hero skills, engine/adapter rules, new backend endpoints, or
  API schema changes.
- A Stage Map redesign, new map art, unrelated Team Builder redesign, or
  change to Arena Battle Rules/configuration behaviour.

## Acceptance Criteria

1. Warrior's Barrack is an accessible enabled Stage Map control positioned on
   its actual map landmark; Arena remains functional and the other locations
   remain inactive.
2. Selecting Warrior's Barrack opens Battle 1 structured preparation, not an
   ordinary Arena builder.
3. Each Barrack builder presents exactly the four allowed player definitions;
   none of the six other approved roster heroes can be assigned in the stage
   builder, while Arena still exposes its normal full roster.
4. Battle 1 is fixed 2v2 against Warrior Defence and Priest Comprehensiveness;
   Battle 2 is fixed 1v1 against Warrior Weapon Master; Battle 3 is fixed 3v3
   against Warrior Defence, Warrior Berserker, and Priest Comprehensiveness.
5. Structured Team Builder visibly and accessibly identifies Warrior's Barrack,
   battle number, fixed format, and fixed enemy team; players cannot edit the
   enemy, enemy control, randomisation, or format.
6. Each structured launch sends only the existing compatible specified-enemy
   configuration with the exact configured team/size and selected permitted
   player IDs. Arena payloads and controls are unchanged.
7. Authoritative friendly victories advance 1 → 2 → 3 → Stage Map. Defeat,
   draw, and round limit expose Retry Battle for that same battle and never
   advance or add penalties/rewards.
8. Temporary state is clearly non-persistent: it is cleared after Battle 3 and
   is not represented as profile, save, resume, progress, unlock, or database
   functionality.
9. The definition/orchestration approach supports adding another structured
   stage by data/configuration rather than copying the entire Team Builder or
   battle lifecycle.
10. Existing live 1v1/2v2/3v3 Arena behaviour, battle creation, completion
    dialog outcome, avatar fallback, and Stage Map navigation remain working.

## Automated Validation

1. Add/update frontend tests for:
   - Barrack enabled-stage configuration, percent geometry, click/Enter/Space
     navigation, and unchanged Arena/remaining inactive stages;
   - exact allowed player roster and all three exact fixed battle definitions;
   - structured mode labels, immutable enemy/format controls, accessible
     fallback cards, and correct existing creation payloads;
   - Arena mode non-regression, including full roster and editable Battle Rules;
   - outcome-aware lifecycle transitions Battle 1 → Battle 2 → Battle 3 →
     `/stages`, plus retry of defeat/draw/round-limit without advancement; and
   - direct/invalid stage-route fallback behaviour and temporary-state cleanup.
2. Extend route, Team Builder, and BattleExperience/BattleScreen tests rather
   than deleting existing coverage. Add a focused structured-stage suite if it
   improves clarity.
3. No Python code should be required. Run targeted Python adapter/API tests to
   demonstrate the configured existing IDs and 1v1/2v2/3v3 specified-team
   requests remain valid; if implementation unexpectedly requires backend
   changes, stop and escalate scope to the project owner before making them.
4. Run affected Vitest suites, full frontend suite, relevant backend pytest
   suite, `npm run typecheck`, `npm run lint`, `npm run build`, and task-scoped
   `git diff --check`. Record exact commands and actual results, separating any
   pre-existing baseline failures.

## Manual Browser Validation

1. At desktop and narrow viewports, open `/stages`; verify Arena and Warrior's
   Barrack are the only enabled landmarks, each has correct hover/focus/cursor
   behaviour, and the Barrack hotspot covers its left-side fortress without
   map distortion or document overflow.
2. Complete the full intended happy path:

```text
Stage Map → Warrior's Barrack → Battle 1 Team Builder → Battle 1 victory
→ Battle 2 Team Builder → Battle 2 victory → Battle 3 Team Builder
→ Battle 3 victory → Stage Map
```

   Verify each builder's title/number/format/enemy, four-hero player matrix,
   non-editable enemy/format, actual launch payload, fallback handling, focus,
   and Battle Screen transition.
3. Exercise defeat/draw/round-limit with deterministic test/setup assistance
   where required. Confirm Retry Battle returns to the same configured battle
   and does not advance or claim persistence.
4. Separately enter Arena and verify its existing free 1v1/2v2/3v3 player and
   enemy configuration, seed, Enter Battle, completion return, and map
   navigation still work. Record console/runtime/network results.

## Documentation/Handoff Requirements

- Update `docs/web-ui/Screen_Flow.md` with the implemented Warrior's Barrack
  sequence and clearly state its temporary/non-persistent scope.
- Update `docs/web-ui/WEB_UI_ARCHITECTURE.md` with stage-definition/session
  ownership, structured versus Arena builder modes, and outcome-aware
  lifecycle boundary.
- Update `docs/web-ui/Style_Guide.md` for the active Barrack hotspot and
  structured builder information/immutable-team treatment only if it differs
  from the existing standard.
- Update `docs/GDD/Game_Design_Document.md` and/or `docs/GDD/Hero_System.md`
  only for the implemented structured training scope and temporary starting
  roster; do not claim persistence/unlocks.
- Do not alter `Player_Data_and_Save_System.md` except a precise cross-reference
  if implementation reveals one is required. Preserve its not-yet-implemented
  save-system boundary.
- Append complete UI-017 evidence to `docs/Codex/Completed.md`: files changed,
  agent contributions, test/manual results, temporary defeat/retry behaviour,
  known persistence limitation, reviewer disposition, and follow-up risks.

## Agent Assignments

### Complexity and Risk

**High frontend lifecycle and stage-flow feature.** It changes navigation,
stage configuration, Team Builder mode/state, Battle Screen completion handoff,
and outcome routing while preserving live battle contracts and Arena. Main
risks are accidentally broadening the structured stage into persistence,
allowing editable fixed teams, progressing on non-victory, losing correct
completion outcome, breaking existing Arena controls, or misplacing the map
hotspot.

### Participating Agents

- `project-manager` — sequence configuration, lifecycle, UI, validation, and
  review work; enforce temporary/non-persistent scope and Arena preservation;
  consolidate evidence and documentation.
- `ui-developer` — own reusable structured-stage configuration, Stage Map
  activation, route/session orchestration, Team Builder modes, outcome-aware
  completion handoff, retry UX, accessibility/responsive styling, and frontend
  tests. Preserve existing payload/API boundaries.
- `test-automator` — own deterministic stage-definition, configuration,
  payload, outcome-transition, retry, route, and Arena non-regression coverage;
  execute automated and browser validation with exact evidence.
- `reviewer` — independently review fixed-team enforcement, outcome authority,
  temporary-state scope, Arena/map regressions, accessibility, documentation,
  and test sufficiency.

### Non-Participating Agents

- `game-engine-developer` — not selected because the existing backend already
  accepts every specified team/format and this task expressly forbids engine,
  adapter, API, persistence, and gameplay changes. Escalate only if testing
  proves an existing valid specified-team request cannot support the approved
  sequence.

## Completion Notes

Do not mark UI-017 complete until the full three-victory browser sequence and
Arena regression have been evidenced, the temporary defeat/retry behaviour is
documented, all selected agents have reported, and the required authoritative
documents/`Completed.md` record actual results.
