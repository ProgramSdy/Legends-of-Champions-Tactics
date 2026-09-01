# Current Task

## Status

Ready for implementation

---

## Task ID

UI-023

## Title

Add Stage-Map Navigation and Engineering Debug Mode; Redesign Arena as a Persistent 12-Battle Run

## Objective

Add accessible Stage Map navigation to the title and Engineering Test &
Debugging pages, create a player-data-independent debugging battle page with
the full registered roster, and replace the player-facing free-form Arena with
an active-save-slot-owned, twelve-node roguelike-style Arena Run MVP.

## Background

The Stage Map is the current post-save-slot hub but has no direct return to the
title scene and no entry to a safe engineering test environment. Its current
Arena destination opens the general Team Builder and permits a player to choose
any available size, enemy mode, control mode, and seed for every individual
battle. That is useful for development but does not provide the owner-approved
Arena Run loop.

The 31 August owner review defines Arena as a 12-battle run: create a fixed
six-hero squad from heroes unlocked in the active local save, preview each
upcoming battle's 1v1/2v2/3v3 size, choose the required subset from the locked
squad, and face a backend-generated computer enemy. Run state must participate
in the existing five-slot save system. The Engineering page must retain the
old free-form experimentation capability without reading, changing, unlocking,
or otherwise depending on player data.

## Requirements

### 1. Stage Map navigation controls

1. Add a semi-transparent spanner/wrench icon button in the Stage Map's upper
   right corner. Its accessible name must identify Engineering Test & Debugging
   and it must route to `/debug`.
2. Add a visually appropriate, clearly labelled title/home-return icon button
   in the upper left corner. It must route to the existing Game Start route
   (`/`), not create a second startup implementation.
3. Both controls must be keyboard reachable, visibly focused, responsive,
   positioned above map art/hotspots without obscuring them, and preserve the
   dark-fantasy visual language. They must not alter hotspot geometry,
   activation, or debug-hotspot behavior.

### 2. Engineering Test & Debugging page

1. Add the dedicated `/debug` page/route. Its starting UI may reuse the
   current free-form Arena Team Builder and Battle Screen visual structure,
   but it must be explicitly presented as Engineering Test & Debugging, not as
   player Arena progress.
2. Both player and enemy team selection must expose every hero returned by the
   registered web/API roster, regardless of the active save slot, unlocked
   heroes, training progress, or whether a save slot exists. Preserve current
   battle-size, formation, Random/Specified enemy, enemy-control, and seed
   tools suitable for testing.
3. Debug battles must use a deliberate debug-only API/creation boundary that
   bypasses player-roster ownership checks but retains normal adapter combat
   validation, legal actions, deterministic seed behavior, event contracts,
   and computer control. Do not weaken the normal Arena or structured-stage
   ownership checks.
4. The debug page must not fetch or mutate progression/save-slot/arena-run
   data, unlock heroes, grant rewards, commit stage victory, or write any
   persistent player data. Ending/reloading a debug battle simply returns to
   its debug builder; active battle sessions remain process-local.
5. Provide a clear route back to Stage Map and preserve existing accessibility,
   fallback assets, and responsive layout.

### 3. Arena Run lifecycle and persistence

1. Replace the player-facing Stage Map Arena flow with an Arena Run hub owned
   by the currently active save slot. Exactly one active or completed run
   record is retained per occupied slot; no active state, squad, schedule, or
   results may cross slots.
2. Arena remains unavailable until the active profile owns at least six
   distinct registered heroes. Display the exact current/required count and
   explain that six unlocked heroes are required. Do not silently use locked,
   static-enemy, or debug-only heroes.
3. When eligible and no active run exists, show a Hero Squad Build step using
   currently unlocked heroes. The player must select exactly six distinct
   definitions, confirm the squad, and start a new run. Persist the chosen
   ordered squad atomically with the run schedule; it becomes immutable until
   the run ends.
4. A run contains exactly 12 ordered, independent battle nodes. Generate and
   persist each node's battle size at run creation using the requested
   per-battle probability distribution: 1v1 20%, 2v2 50%, 3v3 30%. Persisted
   node definitions—not client random choices—remain authoritative across
   reloads. A battle's size is shown before the player chooses its team.
5. The hub exposes the current/upcoming node and completed history sufficiently
   to understand run progress. The player may launch only the next unresolved
   node; later nodes are not playable early. After victory, atomically record
   that node as complete and advance to the next. Defeat, draw, or round-limit
   does not advance the run and permits retry of that same node.
6. A saved active run must resume after page reload, application restart, and
   save-slot switch/load with its locked squad, node schedule, and current
   progress intact. A process-local in-progress battle need not be recoverable;
   reopening the unresolved node creates a fresh session from its persisted
   node definition.
7. After the twelfth friendly victory, mark the run completed and provide a
   clear completion state. A subsequent new run may be started only through a
   clear, intentional New Arena Run action; do not reset a run automatically.
8. No Arena rewards, relics, injury, healing, shop, branching path, elite,
   boss, achievement, difficulty modifier, cloud/account, leaderboard, or
   active-battle save/resume system is in scope.

### 4. Arena team selection and authoritative enemy generation

1. Before each node, reuse/adapt Team Builder so the player selects exactly
   the node's required 1/2/3 heroes from the locked six-hero squad. The player
   cannot add, substitute, or otherwise select a hero outside that squad. In
   2v2/3v3 retain the existing player formation choice; 1v1 has none.
2. The Arena Run UI must show the upcoming size and the backend-authored enemy
   composition/formation summary before battle launch. Remove/disable free-form
   Arena controls that conflict with the node: battle-size selection, random
   versus specified enemy selection, enemy-team editing, enemy control mode,
   and client seed input.
3. Generate enemy team and formation server-side for each persisted node using
   the full registered roster, allowing repeated enemy definitions. Computer
   control is mandatory. The client never supplies/replaces the enemy roster,
   formation, outcome, completion, or run randomness.
4. For a 2v2 node: choose either `side-by-side` with both heroes from the full
   roster, or `front-rear` with the ordered front hero sampled from Warrior or
   Paladin and the ordered rear hero sampled from Mage, Rogue, or Priest.
5. For a 3v3 node: interpret the owner’s “Side by Side” as existing
   `all-front`, with all three heroes sampled from the full roster. For
   `two-front-one-rear` and `one-front-two-rear`, every ordered front position
   must be Warrior or Paladin and every ordered rear position Mage, Rogue, or
   Priest. Preserve the existing formation IDs and adapter ordering semantics.
6. For a 1v1 node, sample one enemy from the full registered roster. Use an
   authoritative persisted seed/node data so reloading or retrying cannot
   change the advertised node's size, formation, or enemy composition.
7. The debug-only ownership bypass is restricted to section 2. Every ordinary
   player route, including Arena Run and structured training, continues to
   enforce the active profile's owned hero roster.

### 5. Data/API and migration safeguards

1. Extend the SQLite progression schema with an explicit, versioned Arena Run
   model linked to profile/save-slot identity. Store immutable squad, 12-node
   schedule/configuration, node completion, lifecycle state, and enough
   server-owned random data to recreate a node consistently. Use transactional,
   idempotent creation and completion operations.
2. Existing UI-021 save-slot progression, training stage indices/rewards, and
   active-slot authority must migrate non-destructively. Slots without an Arena
   Run receive no fabricated history; completed/active data is never copied to
   another slot or silently reset.
3. Define typed API contracts for Arena availability/state, creating a run,
   launching only the current node, and committing only an authoritative
   friendly victory for that run node. Reject invalid slot/profile state,
   insufficient/locked/duplicate squad members, malformed/out-of-order node
   requests, stale profile/session ownership, repeat completion, and
   client-supplied enemy/random/progress data with clear typed errors.
4. Keep training completion distinct from Arena completion. Update the generic
   battle completion route or add a dedicated Arena commit path only where this
   cleanly preserves existing stage semantics and idempotency.

## Out of Scope

- Any work discarded with UI-022; do not restore or recreate that task’s
  event-triggered HUD, targeting, or 2v2-scale changes.
- New hero definitions/art/classes, battle balance, skills, statuses, attack
  types, engine targeting rules, battle-event schema changes, or roster
  expansion beyond the registered ten definitions.
- Arena rewards/relics, campaign/branching, shop/healing/injury, elite/boss,
  difficulty, achievements, online accounts, cloud sync, or active battle
  recovery.
- Altering the five-save-slot count, new-game roster, overwrite behaviour,
  structured curricula/rewards, Stage Map hotspot geometry, or UI-018/UI-019
  formation semantics.
- Editing the owner-controlled
  `docs/web-ui/screenshots_debug/UI_Review_Human.md`.

## Relevant Files

### Stage map, routes, and user interface

- `web-ui/components/stages/StageSelectionScreen.tsx`
- `web-ui/components/stages/stage-config.ts`
- `web-ui/app/stages/page.tsx`, `web-ui/app/page.tsx`, and `web-ui/app/game/page.tsx`
- new `web-ui/app/debug/page.tsx` and debug experience/component modules
- `web-ui/components/battle/BattleExperience.tsx`
- `web-ui/components/battle/TeamBuilder.tsx`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/app/globals.css`

### Contracts, API, and persistence

- `web-ui/lib/battle/types.ts` and `web-ui/lib/battle/liveProvider.ts`
- `battle_api/models.py`, `battle_api/app.py`, and `battle_api/adapter.py`
- `battle_api/progression.py`
- existing save-slot, battle-session, completion, and API fixtures

### Tests and documentation

- `tests/test_ui020_progression.py`, `tests/test_battle_api.py`, and focused
  Arena Run/debug API, persistence, migration, and enemy-generation tests
- `web-ui/tests/ui-012-stage-selection.test.tsx`,
  `web-ui/tests/ui-013-team-builder.test.tsx`,
  `web-ui/tests/ui-020-progression.test.tsx`,
  `web-ui/tests/ui-021-save-slots-and-previews.test.tsx`, and focused new UI tests
- `docs/GDD/Game_Design_Document.md` and `docs/GDD/Combat_System.md`
- `docs/Technical/Player_Data_and_Save_System.md`, `docs/Technical/Architecture.md`,
  and `docs/Technical/Networking.md`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`, `docs/web-ui/Screen_Flow.md`,
  `docs/web-ui/WEB_UI_ARCHITECTURE.md`, and `docs/web-ui/Style_Guide.md`
- `docs/Codex/Completed.md`

## Acceptance Criteria

1. Stage Map has accessible upper-left title/home and upper-right semi-transparent
   Engineering Test & Debugging controls; both routes work without breaking map
   hotspots, keyboard navigation, or responsive rendering.
2. `/debug` exposes the full roster to both sides and free-form test controls
   without a save slot/progression fetch or write. Its debug-only creation API
   permits full-roster testing while normal player APIs still reject locked
   player heroes.
3. An active save with fewer than six unlocked heroes cannot start Arena and
   receives a clear requirement. With six or more, exactly six distinct owned
   heroes are required to start a run and stay immutable through it.
4. A new Arena Run persists exactly 12 server-authored nodes with 20%/50%/30%
   size selection logic; all node size/formation/enemy data remains stable on
   reload/retry and is visible before each launch.
5. Arena player team selection is limited to the locked squad and exact node
   size; free-form enemy/size/control/seed controls are absent. Existing player
   formation selection remains valid for 2v2/3v3.
6. Enemy teams can repeat definitions and meet every stated formation/faculty
   constraint. They are computer-controlled and cannot be forged by the client.
7. Only the current node can launch; only an authoritative friendly victory
   advances it once. Defeat/draw/round-limit retries it. Run state survives
   reload/restart and remains isolated per save slot; twelve victories produce
   a completed state and intentional new-run entry.
8. Existing five-slot, training, ordinary battle, formation, and debug-free
   player-data boundaries have regression coverage and remain functional.

## Validation Required

### Automated

1. Backend: clean and migrated schema tests; active-slot isolation; eligibility;
   exact unique owned squad; atomic run create/resume/retry/complete; 12 nodes;
   deterministic node recreation; out-of-order/stale/repeated completion
   rejection; reload/restart; training coexistence; and no persistence from
   debug battles.
2. Enemy-generation property/seed tests across many runs: 1v1/2v2/3v3 type
   distribution logic, duplicates allowed, computer control, supported IDs,
   and each required front/rear faculty constraint and ordering.
3. API/contract tests: typed arena state/create/launch/commit/errors; no
   client-supplied enemy/progress/random fields; normal ownership enforcement;
   debug-only bypass isolation; existing stage completion unchanged.
4. Frontend: Stage Map controls/routes/focus; debug full roster and no
   progression calls; eligibility and six-squad interactions; locked squad;
   current-node-only flow; preview/configuration rendering; retry/completion;
   save-slot switching/reload; responsive and keyboard checks.
5. Run focused and full relevant backend/frontend suites, TypeScript typecheck,
   ESLint, production build, Python compileall, and task-scoped
   `git diff --check`; record exact commands/results and distinguish inherited
   failures.

### Manual browser validation

1. At desktop and narrow widths, use both new Stage Map controls via pointer
   and keyboard, then verify all three existing map locations still enter the
   correct destinations.
2. Open `/debug` with no active slot and verify both teams can use every roster
   hero, random/specified/control/seed tools work, battles resolve, and no
   player progression/save data changes.
3. Load slots with four, six, and different unlocked rosters. Confirm gating,
   squad selection, persistent node preview, allowed player-team choices,
   computer constrained enemy presentation, retry, save-slot isolation, reload,
   and twelve-node completion/new-run flow.
4. Smoke test structured stages, save selection/overwrite, ordinary battle
   launch, 2v2/3v3 formations, console/network errors, and adapter restart.

## Agent Assignments

### Complexity and risk

**Very high-risk cross-boundary progression feature.** It adds persistent,
randomized run state, player ownership gates, a secure debug bypass, battle
launch/commit boundaries, and routing/UI changes. Main risks are player-data
leakage through debug tools, slot leakage, client-forged enemies/progression,
non-repeatable nodes, duplicate advancement, accidental reset, and regression
to current training/save-slot contracts.

### Participating agents

- `project-manager` — coordinate scope, lifecycle decisions, role handoff,
  migration/slot safety, documentation, and evidence; prevent future features.
- `game-engine-developer` — own versioned SQLite Arena Run schema, seeded
  node/enemy generation, authoritative launch/completion, debug API isolation,
  migrations, contracts, and backend tests.
- `ui-developer` — own Stage Map controls, `/debug`, Arena hub/squad/node UI,
  Team Builder mode separation, accessibility, responsive styling, and frontend
  contracts; never author progression/enemy state locally.
- `test-automator` — own deterministic persistence/seed/property, debug
  isolation, save-slot, lifecycle, accessibility, responsive, and regression
  evidence.
- `reviewer` — independently audit authority, duplicates, save isolation,
  debug no-write boundary, formation constraints, migration, accessibility,
  documentation, and deferred scope.

## Completion Notes

Do not mark UI-023 complete until all selected roles report; clean and migrated
databases prove per-slot Arena isolation and idempotent lifecycle; debug is
proven save-independent; every node/enemy constraint is validated; browser
evidence covers the controls, gating, squad, node/retry/completion flows; and
existing save, training, battle, and formation contracts pass. Append exact
files, validation commands/results, reviewer decision, known risks, and
deferred features to `docs/Codex/Completed.md`.
