# Current Task

## Status

Complete

---

## Task ID

UI-020

## Title

Add Paladin's Altar and Persistent Nine-Battle Training Progression

## Objective

Activate Paladin's Altar on the Stage Map, replace Warrior's Barrack with its
owner-approved nine-battle sequence, and introduce the smallest
backend-authoritative persisted progression slice needed to unlock the five
specified heroes and grant the one stated item card reward.

## Background and Authoritative Interpretation

The owner review dated 2026-08-19 defines two structured training stages:
Paladin's Altar and Warrior's Barrack. Each has nine fixed battles. The listed
heroes are the fixed **predefined enemy team**, in ordered slots; the player
continues to choose a permitted friendly team from their currently unlocked
roster. This follows the existing structured-stage Team Builder model.

The existing live roster currently exposes all ten definitions and UI-017's
Warrior's Barrack is a temporary three-battle frontend session. That does not
meet the new unlock requirement: unlocks must remain available after page
reload/restart and must not be invented by React. This task therefore authorizes
the first minimal backend-owned persisted progression implementation. It must
remain compatible with the design principles in
`docs/Technical/Player_Data_and_Save_System.md` without prematurely implementing
full profiles, active-battle recovery, inventory/equipment, rewards economy,
or cloud/account functionality.

Use these existing stable IDs; review spelling is normalized only where it is
an obvious typo:

- `Warrior_Baserker` → `hero.warrior.berserker`
- `Priest_Descipline` → `hero.priest.discipline`
- 3v3 “Side by Side” → existing `all-front` (all three positions are `front`)
- 3v3 “Front 2 and Rear 1” → existing `two-front-one-rear`

The required initially locked player definitions are:

- `hero.paladin.protection`
- `hero.paladin.retribution`
- `hero.paladin.holy`
- `hero.warrior.berserker`
- `hero.warrior.defence`

The remaining approved live definitions are initially selectable. Locked
definitions remain valid static content and fixed stage enemies, but must not
be selectable in Arena/structured player matrices until their authoritative
unlock is returned.

## Stage Definitions

### Paladin's Altar

1. Activate `paladins-altar` using the existing Valley of Champions artwork.
   Add a percentage-based hotspot over the right-middle altar landmark, using
   the same accessible visual treatment and debug-hotspot method as Warrior's
   Barrack; do not change map art or create a new stage image.
2. Its battles are:

| # | Format / formation | Fixed ordered enemy definitions | Friendly-victory reward |
|---:|---|---|---|
| 1 | 2v2 / `front-rear` | Paladin Protection, Mage Comprehensiveness | none |
| 2 | 1v1 | Paladin Protection | none |
| 3 | 3v3 / `two-front-one-rear` | Paladin Protection, Warrior Defence, Mage Comprehensiveness | unlock Paladin Protection |
| 4 | 2v2 / `side-by-side` | Paladin Retribution, Warrior Weapon Master | none |
| 5 | 1v1 | Paladin Retribution | none |
| 6 | 3v3 / `two-front-one-rear` | Paladin Protection, Paladin Retribution, Priest Discipline | unlock Paladin Retribution |
| 7 | 2v2 / `side-by-side` | Paladin Holy, Rogue Comprehensiveness | none |
| 8 | 1v1 | Paladin Holy | none |
| 9 | 3v3 / `all-front` | Paladin Retribution, Paladin Protection, Paladin Holy | unlock Paladin Holy |

### Warrior's Barrack

Replace its current three battles with this nine-battle sequence:

| # | Format / formation | Fixed ordered enemy definitions | Friendly-victory reward |
|---:|---|---|---|
| 1 | 2v2 / `front-rear` | Warrior Berserker, Priest Comprehensiveness | none |
| 2 | 1v1 | Warrior Berserker | none |
| 3 | 3v3 / `two-front-one-rear` | Warrior Berserker, Rogue Comprehensiveness, Mage Comprehensiveness | unlock Warrior Berserker |
| 4 | 2v2 / `side-by-side` | Warrior Berserker, Warrior Weapon Master | none |
| 5 | 1v1 | Warrior Weapon Master | none |
| 6 | 3v3 / `two-front-one-rear` | Warrior Weapon Master, Paladin Retribution, Priest Discipline | grant one item card |
| 7 | 2v2 / `front-rear` | Warrior Defence, Priest Discipline | none |
| 8 | 1v1 | Warrior Defence | none |
| 9 | 3v3 / `all-front` | Warrior Weapon Master, Warrior Defence, Warrior Berserker | unlock Warrior Defence |

## Requirements

### 1. Structured-stage data and flow

1. Evolve the existing reusable structured-stage data model rather than adding
   stage-specific component conditionals. It must express fixed battle size,
   fixed enemy IDs, fixed formation for both sides, ordered sequence, and an
   optional completion reward.
2. Structured battles must not expose editable battle size, enemy composition,
   enemy control, randomisation, or formation controls. Launch the exact fixed
   size/team/formations with computer enemy control through the existing typed
   battle-create contract.
3. Progress only on the authoritative friendly-victory outcome. Defeat, draw,
   and round limit retry the same battle; they award no reward and do not alter
   later battle access.
4. A completed battle unlocks only the next battle in that stage. Completing
   Battle 9 records the stage complete and returns to Stage Map. The player may
   revisit completed battles, but cannot skip locked sequence steps or duplicate
   a reward.
5. The stage builder shows stage name, Battle N of 9, fixed format/formation,
   fixed enemy summary, current unlock/reward context, and clear locked-step
   state. Maintain fallback artwork, keyboard operation, focus, responsive
   layout, and existing formation presentation.

### 2. Persisted progression and roster gating

1. Implement a small backend-owned local persistence boundary (SQLite or the
   existing project-approved backend persistence abstraction) with an explicit
   stable default local player/profile identity. Do not store progression in
   localStorage as the authority.
2. Persist and return, at minimum:
   - unlocked hero definition IDs;
   - per-stage highest completed/unlocked battle index and completed state; and
   - granted item-card reward identities/counts.
3. Define one stable generic item-card reward ID for Warrior's Barrack Battle 6
   (for example `reward.item-card.basic`) with no combat effect, inventory
   screen, equipment behavior, card artwork, or invented item name. Persist it
   once and show its earned state. This task authorizes only the required
   “You have granted an item card” notification.
4. Expose typed progression/roster availability through the adapter API. The
   frontend fetches and renders it; it must never compute an unlock from the
   visible battle number or dialog text.
5. Apply player ownership filtering consistently to Arena and structured-stage
   friendly selection matrices. Fixed stage enemies bypass player ownership
   filtering but remain validated against the static roster.
6. Make reward application idempotent and atomic with the authoritative battle
   completion/progression update. A reload, repeated completion callback, retry,
   or revisiting a completed battle must not grant duplicate heroes/cards or
   advance extra steps.
7. Seed/initialize the default progression deterministically with the five
   stated heroes locked and every other approved live definition available.
   Clearly handle missing/corrupt progression storage with a retryable,
   non-silent error; do not silently reset earned progress.

### 3. Reward feedback and availability

1. After a first successful reward commit, show an accessible modal/notification
   before continuing:
   - `Paladin_Protection is unlocked`
   - `Paladin_Retribution is unlocked`
   - `Paladin_Holy is unlocked`
   - `Warrior_Baserker is unlocked`
   - `Warrior_Defence is unlocked`
   - `You have granted an item card`
2. Use player-facing display text with the project’s normal typography; retain
   the owner-provided messages above in the notification body. The stable
   definition/reward IDs—not those strings—are authoritative.
3. Once dismissed, continue to the next permitted stage step or Stage Map as
   appropriate. A previously earned reward may be shown as already earned but
   must not re-open a misleading new-reward modal on replay.
4. Newly unlocked heroes must become selectable immediately after the refreshed
   authoritative progression state is received, and remain selectable after a
   full reload/restart.

### 4. Stage Map and compatibility

1. Arena, Warrior's Barrack, and Paladin's Altar are the only enabled map
   locations. Mage's Tower, Rogue's Forest, and Priest's Cathedral remain
   inactive and visually untouched.
2. Preserve UI-018/UI-019 2v2/3v3 formation contracts, target legality,
   attack-type behavior, snapshot positions, and formation presentation.
3. Preserve existing live battle API contracts except for narrowly typed,
   additive player-progression endpoints/data genuinely required by this task.
   Do not put profile/stage/reward data into `BattleCreateConfiguration`.

## Out of Scope

- Multiple-profile UI, profile naming/deletion, login, cloud sync, online/PvP,
  active-battle checkpoint/resume/abandonment, replay, or account migration.
- Item-card content, art, inventory, equipping, effects, economy, currencies,
  or additional rewards/unlocks.
- New hero definitions, hero skill/attack-type changes, balance changes,
  formation changes, stage-map artwork, or unrelated Team Builder redesign.
- Activating Mage's Tower, Rogue's Forest, or Priest's Cathedral.
- Editing the owner-controlled `UI_Review_Human.md`.

## Relevant Files

### Frontend

- `web-ui/components/stages/stage-config.ts`
- `web-ui/components/stages/StageSelectionScreen.tsx`
- `web-ui/components/stages/structured-stage-config.ts`
- `web-ui/components/battle/BattleExperience.tsx`
- `web-ui/components/battle/TeamBuilder.tsx`
- `web-ui/lib/battle/liveProvider.ts` and `web-ui/lib/battle/types.ts`
- `web-ui/app/globals.css`

### Backend and persistence

- `battle_api/app.py`, `battle_api/models.py`, and `battle_api/adapter.py`
- a narrowly scoped new backend progression/store module and its database file
  handling/migration boundary
- existing static roster/hero definitions and relevant battle completion path

### Tests and documentation

- `tests/test_battle_api.py`, `tests/test_battle_adapter.py`, and focused new
  progression/stage tests
- `web-ui/tests/ui-012-stage-selection.test.tsx`,
  `web-ui/tests/ui-017-stage-and-structured-config.test.tsx`, and focused new
  Team Builder/BattleExperience/Stage Map suites
- `docs/GDD/Game_Design_Document.md`, `docs/GDD/Hero_System.md`,
  `docs/Technical/Player_Data_and_Save_System.md`, `docs/Technical/Architecture.md`,
  `docs/web-ui/PYTHON_ADAPTER_API.md`, `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`,
  `docs/web-ui/Screen_Flow.md`, `docs/web-ui/WEB_UI_ARCHITECTURE.md`, and
  `docs/web-ui/Style_Guide.md`

## Acceptance Criteria

1. Paladin's Altar is an enabled, accessible right-middle altar hotspot with
   the same approved map treatment as Warrior's Barrack; only Arena and these
   two stages are enabled.
2. Both stages present exactly the nine specified fixed battles, exact ordered
   enemy teams, fixed formations, and Battle N of 9 progression.
3. Friendly victory is the only progression/reward trigger; non-victories
   retry the same battle, and locked steps cannot be entered or skipped.
4. The five named heroes start unavailable to player selection, unlock only at
   their specified Battle 3/6/9 rewards, immediately become selectable after
   the committed reward, and remain so after reload/restart.
5. Warrior's Barrack Battle 6 grants one persistent generic item card exactly
   once, displays the required notification, and grants no unrequested power
   or item behavior.
6. Stage enemies use every specified definition/formations even when that hero
   is still locked to the player; no missing roster ID is silently substituted.
7. Existing Arena configuration, all approved battle sizes/formations,
   API/engine combat rules, status/attack-type behavior, fallback assets, and
   current battle presentation remain functional.
8. The backend is the source of truth for progression/unlocks/rewards. Browser
   reload/restart cannot lose or duplicate a committed reward, and corrupt or
   unavailable data surfaces a clear retryable failure.

## Validation Required

### Automated

1. Backend tests for database/schema initialization; default locked roster;
   typed progression fetch; stage/battle access; exact reward mapping;
   atomic/idempotent completion; restart persistence; duplicate/retry/replay
   defense; corrupt/missing-store errors; and static-stage enemy bypass.
2. Adapter/API tests for exact nine battle definitions/formation payloads,
   additive progression endpoint schemas, input validation, and no modification
   of existing live-battle request/snapshot contracts.
3. Frontend tests for Stage Map activation/inactive regression; structured
   Battle 1–9 labels/locked state/fixed composition/formation; friendly-matrix
   ownership gating; reward modal semantics; immediate refresh; retry paths;
   Browser reload persistence seam; responsive/focus/fallback behavior; and
   Arena/UI-018/UI-019 regressions.
4. Run focused and full backend pytest, affected/full frontend suites,
   TypeScript typecheck, lint, production build, Python compilation, and
   task-scoped `git diff --check`. Record actual commands/results and separate
   inherited failures.

### Manual browser validation

1. Open `/stages` at desktop and narrow widths: verify only Arena, Warrior's
   Barrack, and Paladin's Altar are active, and tune/verify the altar hotspot
   against the actual map landmark without distortion.
2. Start from a clean deterministic default store; verify five heroes are
   absent/locked in player selection but can appear as fixed stage enemies.
3. Complete every third/sixth/ninth reward boundary in both stages using
   deterministic test assistance. Verify exact notification text, next-stage
   state, immediate selectable hero change, one-time item card, reload/restart
   persistence, and no duplicate on replay.
4. Exercise defeat, draw, round limit, browser refresh, stage exit/re-entry,
   and an unavailable/corrupt storage simulation. Confirm no false advancement
   or reward and a clear recovery/error path.
5. Smoke test Arena and at least one 1v1/2v2/3v3 battle in each stage,
   including fixed formations and target/effect presentation. Record console,
   runtime, and network errors.

## Documentation/Handoff Requirements

- Update GDD stage/training, hero-unlock, and reward scope; document only the
  implemented generic item-card behavior and no invented item mechanics.
- Update `Player_Data_and_Save_System.md` and `Architecture.md` to distinguish
  this implemented minimal default-profile progression store from deferred
  profiles/recovery/cloud functionality.
- Update API/data contract, Screen Flow, web UI architecture, and style guide
  for progression endpoints/data, roster ownership gating, stage access,
  reward feedback, and the altar hotspot.
- Append UI-020 completion evidence to `docs/Codex/Completed.md`: files,
  role work, persistence/idempotency evidence, exact test/browser results,
  reviewer disposition, migration/storage risks, and deferred save features.

## Agent Assignments

### Complexity and risk

**Very high-risk cross-boundary progression feature.** It combines Stage Map
navigation, structured battles, formation payloads, roster availability,
backend persistence, atomic reward logic, and user-visible unlock feedback.
The main risks are temporary unlocks, duplicate rewards, corrupt/reset data,
frontend-authoritative progression, bypassed locked steps, mutable fixed teams,
or regression to live combat/formation behavior.

### Participating agents

- `project-manager` — coordinate stage, persistence, UI, API, migration, and
  validation work; enforce the owner-approved scope and resolve data boundaries.
- `game-engine-developer` — own progression storage/API, atomic/idempotent
  reward/progression updates, battle outcome authority, roster availability,
  migrations/errors, backend tests, and technical/GDD documentation.
- `ui-developer` — own Stage Map activation, reusable nine-battle config,
  locked/unlocked matrix presentation, reward dialog, progression fetch/refresh,
  accessibility/responsive behavior, and frontend tests; never derive rewards.
- `test-automator` — own clean-store/restart/idempotency/error, battle-sequence,
  request/formation, unlock/reward, UI, and regression validation evidence.
- `reviewer` — independently review persistence ownership, migration/error
  safety, atomicity/idempotency, stage data accuracy, UI accessibility, API
  compatibility, deferred-scope protection, and documentation/test quality.

## Completion Notes

Do not mark UI-020 complete until all selected roles report, both complete
nine-battle curricula are evidenced, the five hero unlocks and one item-card
grant survive restart without duplication, locked-roster and fixed-enemy
behaviour are validated, and Arena/UI-018/UI-019 regressions are documented.
