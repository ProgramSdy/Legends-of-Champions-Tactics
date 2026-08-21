# Current Task

## Status

Complete

---

## Task ID

UI-021

## Title

Add Five-Slot Save Selection and Correct Structured-Stage Previews

## Objective

Replace the startup page's direct Stage Map entry with a five-slot New Game /
Load Game flow, make the selected slot the authoritative owner of UI-020
progression, and correct the Team Builder preview crops for Warrior's Barrack
and Paladin's Altar so each shows its actual map building.

## Background

UI-020 introduced a minimal SQLite-backed **default** profile that persists
unlocked heroes, structured-stage progress, and the generic item-card reward.
The current startup `START GAME` link goes directly to `/stages`; no profile or
slot selector exists. This task expands that completed persistence boundary to
exactly five local save slots. It does not authorize online accounts, cloud
sync, active-battle recovery, or a broad profile-management system.

The project owner defines every newly initialized game to begin with exactly
these available player heroes:

- `hero.warrior.weapon_master` — Warrior Weapon Master
- `hero.mage.comprehensiveness` — Mage Comprehensiveness
- `hero.priest.comprehensiveness` — Priest Comprehensiveness
- `hero.rogue.comprehensiveness` — Rogue Comprehensiveness

All other approved roster definitions begin locked in a newly created slot and
are available only through the implemented training rewards. Fixed structured
stage enemies remain independent of player ownership.

To preserve existing UI-020 progress, migrate the existing default-profile
record into the first empty save slot on first schema upgrade. The migration
must be atomic/idempotent, must not create a duplicate copy on restart, and
must surface a non-silent recovery error if it cannot preserve the record.

The existing Team Builder currently uses `valley_of_champions.png` with one
generic scale/crop determined from stage geometry. That crop does not cleanly
show either selected building. Stage-map hotspot geometry and preview crop
focus are separate concerns: keep the current interactive hotspot locations;
add explicit stage-preview focus data and tune it against the existing map art.

## Requirements

### 1. Startup flow

1. Activating `START GAME` opens an accessible modal/panel with two choices:
   **NEW GAME** and **LOAD GAME**. It must not navigate to Stage Map until a
   valid save-slot action finishes.
2. **NEW GAME** opens a five-slot selector. Empty slots are available for a
   fresh game. Occupied slots are visibly identified as occupied and may only
   be selected after a clear overwrite confirmation that names the exact slot
   and states that its saved progression will be permanently replaced.
3. **LOAD GAME** opens the same five-slot selector filtered/enabled only for
   occupied slots. When no saved slot exists, LOAD GAME is disabled with a
   readable explanation; it must not open a dead-end dialog.
4. A successful New Game creates/initializes the selected slot with the exact
   four-hero starting roster and zero stage/reward progress, selects it as the
   active slot, then routes to `/stages`.
5. A successful Load Game selects the existing slot as active, loads its
   authoritative progression, then routes to `/stages`. It must not reset,
   reinitialize, or grant starter state to that slot.
6. Support Escape/Cancel, focus trapping/restoration, clear loading/error
   feedback, keyboard-only selection, and responsive layout. Confirming an
   overwrite is destructive; cancelling it must make no write.

### 2. Five-slot persistence model

1. Extend the UI-020 backend persistence schema/store from one default profile
   to exactly five stable local slots (`1`–`5`). A slot stores occupied state,
   stable profile identity, creation/last-played metadata suitable for the
   selector, progression, unlocked heroes, stage state, and rewards.
2. The backend owns the active-slot selection. The client may request New,
   Load, or confirmed Overwrite, then renders the returned active profile and
   progression. Do not treat URL query parameters, localStorage, or React state
   as the authoritative selected save.
3. All existing UI-020 progression APIs and structured-stage victory commits
   must operate on the active slot only. Switching slots must never leak stage
   progress, heroes, rewards, cached UI state, or live provider/session state
   between slots.
4. Define typed APIs/contracts for listing five slot summaries, creating a new
   slot, loading/selecting an occupied slot, and overwriting a specific occupied
   slot. Reject slot IDs outside 1–5, loading empty slots, creating into an
   occupied slot without explicit confirmed overwrite, and client-supplied
   progression/reward data.
5. Schema initialization/migration must preserve UI-020 default-profile data
   exactly once. Backend failures, lock/contention, corrupt/missing database,
   and impossible migration state must produce a retryable typed error; never
   silently reset, select another slot, or overwrite existing data.
6. Do not introduce profile names, delete-slot controls, profile settings,
   account/login, multiplayer identity, cloud sync, active battle checkpoints,
   or any storage beyond five local game slots.

### 3. Roster and progression compatibility

1. A new slot has exactly the four starting heroes above. It has no unlocked
   Paladin Protection/Retribution/Holy, Warrior Berserker/Defence, or item-card
   reward until earned through existing UI-020 stage victory commits.
2. Existing migrated/default progress must retain its actual earned hero IDs,
   stage indices/completion, and item-card count; do not retroactively reset it
   to starter state.
3. Team Builder Arena and structured friendly matrices use the active slot's
   authoritative roster availability. Predefined structured enemies may still
   use locked static definitions.
4. Stage Map and Team Builder must refresh active-slot progression after New,
   Load, overwrite, reward commits, and a page reload. Existing UI-020 reward
   idempotency and formation/battle contracts remain unchanged.

### 4. Correct Current Stage previews

1. Add presentation-only preview focus metadata to the canonical enabled-stage
   definition, separate from clickable hotspot geometry.
2. In Team Builder for **Warrior's Barrack**, crop the existing Valley of
   Champions art to clearly show the actual left-side red-banner Barrack
   building. For **Paladin's Altar**, crop it to clearly show the actual
   right-middle altar building. Keep Arena's existing useful preview intact.
3. Use CSS/object-position, transform origin, or an equivalent responsive crop
   approach. Do not create, edit, stretch, or replace stage-map artwork, and do
   not reuse a generic map-centre crop.
4. At desktop and narrow widths, preserve the building as the visual focal
   point while keeping the Current Stage label legible, avoiding empty space,
   distortion, overflow, or hiding the building under the text gradient.

## Out of Scope

- More/fewer than five save slots, profile names, rename/delete UI, accounts,
  login, cloud synchronization, online/PvP, or multi-device save merging.
- Active-battle save/resume/abandonment, automatic checkpoints, replay, or
  changes to battle-session persistence.
- New rewards, item behavior/art/inventory/equipment, new heroes, skill or
  attack-type changes, balance, stage curriculum changes, or map artwork.
- Changes to current Stage Map hotspot geometry except a focused correction if
  browser evidence proves an existing hotspot itself is wrong.
- Editing the owner-controlled `UI_Review_Human.md`.

## Relevant Files

### Startup, routing, and UI

- `web-ui/app/page.tsx`
- `web-ui/components/startup/StartupScreen.tsx`
- `web-ui/components/stages/StageSelectionScreen.tsx`
- `web-ui/components/stages/stage-config.ts`
- `web-ui/components/battle/BattleExperience.tsx`
- `web-ui/components/battle/TeamBuilder.tsx`
- `web-ui/lib/battle/liveProvider.ts` and `web-ui/lib/battle/types.ts`
- `web-ui/app/globals.css`

### Backend/persistence

- `battle_api/progression.py`
- `battle_api/app.py`, `battle_api/models.py`, and `battle_api/adapter.py`
- current UI-020 progression schema/database migration and tests

### Tests and documentation

- `tests/test_ui020_progression.py`, `tests/test_battle_api.py`, and focused
  new save-slot/migration tests
- `web-ui/tests/ui-020-progression.test.tsx`, startup/Stage Map/Team Builder
  suites, and focused new save-slot/preview tests
- `docs/GDD/Game_Design_Document.md`, `docs/GDD/Hero_System.md`,
  `docs/Technical/Player_Data_and_Save_System.md`, `docs/Technical/Architecture.md`,
  `docs/Technical/Networking.md`, `docs/web-ui/PYTHON_ADAPTER_API.md`,
  `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`, `docs/web-ui/Screen_Flow.md`,
  `docs/web-ui/WEB_UI_ARCHITECTURE.md`, and `docs/web-ui/Style_Guide.md`

## Acceptance Criteria

1. START GAME presents New Game and Load Game; Load Game is disabled only when
   all five slots are empty.
2. New Game creates a selected empty slot with exactly the four stated heroes,
   starts zero training/reward progress, selects that slot, and enters Stage
   Map. Overwriting an occupied slot requires exact-slot confirmation and
   resets only that slot after confirmation.
3. Load Game lists/selects only occupied slots and restores the selected slot's
   own authoritative stage progress, unlocked heroes, and reward state.
4. Exactly five local slots exist. Slot isolation holds across backend API,
   restart/reload, arena roster availability, stage progression/rewards, and
   frontend cache/provider state.
5. Existing UI-020 default progress migrates exactly once into an available
   slot with no loss or duplication; failure is clear and retryable.
6. Warrior's Barrack and Paladin's Altar Current Stage previews each visibly
   show their correct building from the existing Stage Map at representative
   desktop/narrow viewports. Arena and Stage Map hotspots remain functional.
7. UI-018/UI-019 formations, UI-020 nine-battle curricula/rewards, existing
   API/battle contracts, accessibility, and fallback presentation regressions
   are absent.

## Validation Required

### Automated

1. Backend tests: five-slot schema/init/listing; valid/invalid slot IDs;
   new/load/confirmed-overwrite flows; empty-load rejection; cancellation/no
   write; selected-slot isolation; restart persistence; exact starter roster;
   legacy default migration/idempotency/rollback; UI-020 reward integration;
   database failure/lock/corruption behavior.
2. API/contract tests: typed slot summaries/actions/errors; no client-created
   progression payload; active-slot progression endpoints; existing battle and
   victory APIs unchanged.
3. Frontend tests: startup modality/focus/Escape/disabled Load; empty/occupied
   slots; overwrite warning/cancel/confirm; route only after success; immediate
   active-slot roster/progression refresh; reload/switch isolation; stage
   preview focus data and responsive crop hooks; no regressions to current
   startup Stage Map/Team Builder flow.
4. Run focused and full backend pytest, affected/full frontend suites,
   typecheck, lint, production build, Python compilation, and task-scoped
   `git diff --check`. Record exact commands/results and separate baselines.

### Manual browser validation

1. With a clean database, confirm Load Game is disabled; create games in all
   five slots, verify their independent starter state, then confirm New Game
   overwriting requires/can cancel the warning and affects only the chosen slot.
2. Earn distinct progress/rewards in at least two slots, restart browser and
   adapter, load each slot, and verify no data crosses between them. Confirm
   current UI-020 migrated data is retained in one slot during upgrade testing.
3. At desktop and narrow widths, inspect startup dialogs, keyboard focus,
   error/retry behavior, and the Barrack/Altar Current Stage previews. Verify
   the actual landmark building is clear, unstretched, and not obscured by the
   label overlay.
4. Smoke test Arena and structured 1v1/2v2/3v3 launch/progression after slot
   creation/loading; record console, network, and runtime errors.

## Documentation/Handoff Requirements

- Update GDD and Hero System for the four-hero new-game roster and the
  implemented five-slot local save boundary.
- Update Player Data/Save System, Architecture, and Networking with the exact
  UI-020 migration, five-slot scope, selected-slot authority, destructive
  overwrite guarantees, and explicitly deferred profile/recovery/cloud work.
- Update API/data-contract, Screen Flow, web UI architecture, and Style Guide
  for the startup save selection, slot endpoints/errors, roster refresh, and
  stage-specific preview-crop ownership.
- Append UI-021 completion evidence to `docs/Codex/Completed.md`: exact files,
  migration and slot-isolation results, validation commands, reviewer decision,
  known database/migration risks, and deferred scope.

## Agent Assignments

### Complexity and risk

**Very high-risk persistence and entry-flow feature.** It changes the first
player interaction, replaces the sole progression identity with five isolated
records, includes destructive overwrite, and must migrate real existing data
without touching live battle rules. Main risks: data loss/duplicate migration,
slot leakage, accidental overwrite, UI-only active profile, stale progression
after switch, broken startup accessibility, and incorrect artwork crops.

### Participating agents

- `project-manager` — coordinate migration, persistence, startup/UI, preview,
  validation, and documentation; enforce five-slot/no-scope-expansion limits.
- `game-engine-developer` — own SQLite/schema migration, active-slot authority,
  typed APIs/errors, transaction/idempotency/isolation, backend tests, and
  technical/GDD documentation.
- `ui-developer` — own startup panels/dialogs, active-slot refresh/routing,
  accessible destructive confirmation, stage-preview focus/cropping, styling,
  and frontend tests; never author progression locally.
- `test-automator` — own clean/migrated/occupied database, overwrite/cancel,
  restart/isolation/error, UI-020 regression, crop, keyboard, and build/test
  evidence.
- `reviewer` — independently review data preservation, destructive-action
  safety, active-slot ownership, API compatibility, accessible flow, crop
  fidelity, test sufficiency, and deferred-scope protection.

## Completion Notes

Do not mark UI-021 complete until all selected roles report; clean and migrated
databases have proven five-slot isolation and non-duplicating migration;
overwrite cancellation/confirmation is demonstrated; exact four-hero new-game
rosters are evidenced; and both structured-stage previews visibly show their
correct buildings without regressions to UI-018, UI-019, or UI-020.
