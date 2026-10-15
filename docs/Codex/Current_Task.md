# Current Task

**Status:** Completed

**Task:** UI-029 — Shadow Evasion Battlefield Transparency Effect

**Owner request date:** 2026-10-15

## Objective

When Rogue Comprehensiveness uses **Shadow Evasion**, make that Rogue's
battlefield figure visibly half transparent for the full authoritative lifetime
of `status.shadow_evasion`. Return the same figure to its normal appearance as
soon as that status is removed or expires.

The effect is a status-state presentation, not a momentary cast animation. It
must work for player and enemy Rogues in 1v1, 2v2, and 3v3 without changing any
combat rule, duration, evasion calculation, skill cooldown, targeting, or
status behaviour.

## Background

Shadow Evasion is implemented by `Rogue_Comprehensiveness.shadow_evasion()`.
It applies the existing engine-owned `shadow_evasion` status, gives it a
duration through `shadow_evasion_buff_duration`, and the status manager later
cleans it up. The battle adapter publishes it as stable
`status.shadow_evasion` with buff presentation, and frontend combatants already
receive their current `statuses` in each snapshot.

`BattlefieldFigure` currently renders the battlefield figure via
`AssetImage`/`.figure-art`; this is the presentation boundary to extend. Do not
make the visual depend on battle-log wording, a locally scheduled timeout,
skill-name matching, presentation-queue timing alone, or a duplicated duration
calculation.

## Requirements

1. Read the current battle renderer, snapshot/status contract, adapter status
   serialization, Shadow Evasion implementation, expiry path, status icon
   metadata, affected CSS, existing tests, and all required project rules
   before editing.
2. Determine whether the existing `CombatantState.statuses` reliably exposes
   the active stable ID `status.shadow_evasion` during the whole duration and
   immediately after removal. If it does, consume that data directly. If it
   does not, make the smallest additive adapter/contract correction required;
   do not infer status from logs or introduce parallel client state.
3. Add a clearly named, status-derived class/data attribute to only the active
   Rogue battlefield figure. Apply an approximately 50% visual opacity to the
   figure artwork while preserving the normal hero footprint, positioning,
   scale, side mirroring, formation layering, target button hit area, health
   display, selected-target highlight, attack/heal/buff/debuff effects, and
   accessibility text.
4. The figure must fade or otherwise transition cleanly into and out of the
   state, but must not flicker, remain faded after expiry/death/replacement,
   cause a layout shift, alter z-index/depth, or reduce command/target
   usability. Keep the existing dark-fantasy visual language. Do not introduce
   a new image asset unless it is demonstrably necessary.
5. The change applies only to the battlefield Rogue figure. Existing sidebar
   portraits, Hero Gallery assets, active-hero card, status icon, skill card,
   audio, and unrelated Rogue visuals must remain unchanged unless a small
   documented accessibility/contract adjustment is genuinely required.
6. Preserve the authoritative status lifecycle. Shadow Evasion should become
   transparent only after its authoritative status is present and return to
   normal as soon as it is absent, including normal expiry and any existing
   authoritative removal path. It must not use a guessed number of rounds.
7. Keep all current status presentation, Battle Information Transparency,
   formation, battle event, API, save, and game-mechanics behaviour intact.

## Out of Scope

- Changing Shadow Evasion's evasion value, duration, cooldown, AI priority,
  damage, target rules, status name, or combat log wording.
- Adding invisibility mechanics, hiding the hero, modifying portraits/cards,
  redesigning generic buffs, or applying transparency to other statuses.
- New art, backend refactors, a new API version, duplicated UI timers, or
  unrelated battle-screen styling work.

## Relevant Files

- `heroes/rogue.py`, `heroes/hero.py`, and
  `game/status_effect_manager.py` — existing authoritative application and
  expiry only; inspect before deciding whether any engine change is needed.
- `battle_api/adapter.py`, `battle_api/models.py`, and battle API/adapter
  status tests — stable status serialization and snapshot authority.
- `web-ui/components/battle/BattleScreen.tsx`,
  `web-ui/lib/battle/types.ts`, `web-ui/lib/battle/assets.ts`, and
  `web-ui/app/globals.css` — battlefield figure state and styling boundary.
- Existing battle renderer/status/formation tests plus
  `tests/test_battle_api.py` and `tests/test_battle_adapter.py`.
- `docs/GDD/Combat_System.md`, `docs/Technical/Architecture.md`,
  `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`,
  `docs/web-ui/PYTHON_ADAPTER_API.md`,
  `docs/web-ui/WEB_UI_ARCHITECTURE.md`, and `docs/web-ui/Style_Guide.md` as
  applicable to final stable behaviour.

## Acceptance Criteria

1. A Rogue's battlefield artwork becomes visibly about half transparent while
   its current snapshot includes `status.shadow_evasion`.
2. It returns to normal immediately after that status is authoritatively
   removed/expires, with no stale opacity in later turns, after defeat, or when
   a different hero occupies a view slot.
3. The effect is correct for friendly and enemy Rogue figures and remains
   correct in 1v1, 2v2, and all 3v3 formations.
4. Figure scale, visual depth, target selection, hover/focus/keyboard control,
   health/status UI, animation/effect layers, and existing status icons remain
   usable and visually coherent.
5. The implementation has one authoritative source of truth: published active
   status data. It neither changes engine mechanics nor infers duration from
   logs, cast timing, or a frontend countdown.
6. Relevant technical/contract/style documentation is updated only where the
   user-visible status presentation or architecture boundary requires it.

## Validation Required

- Add/update deterministic engine/adapter coverage proving Shadow Evasion is
  serialized as active while present and absent after normal expiry/removal;
  verify no mechanics, duration, RNG, events, or unrelated status data changed.
- Add frontend regression tests for active/inactive snapshots, friendly/enemy
  Rogues, status removal, figure-only scope, and preservation of targeting and
  existing figure classes/effects. Cover a multi-hero formation case to guard
  layering/slot regressions.
- Run relevant backend adapter/API/status tests and battle renderer/frontend
  tests, then typecheck, lint, production build, and `git diff --check`.
- Manually check the live or deterministic battle view at desktop and narrow
  viewport: cast Shadow Evasion, observe the sustained approximately 50%
  transparency, observe normal appearance after expiry, and confirm an enemy
  Rogue and a 2v2/3v3 formation. Record exact evidence honestly.

## Agent Assignments

**Complexity/risk:** Moderate. The visual change is small, but it depends on a
live engine → adapter → typed battle snapshot → renderer status lifecycle;
an incorrect shortcut can leave a hero permanently faded or duplicate combat
authority. All five roles are selected to satisfy the project status-integration
gate and independently validate lifecycle correctness.

- **project-manager:** map the status lifecycle, coordinate the cross-boundary
  work, control scope, and consolidate documentation/completion evidence.
- **game-engine-developer:** verify the authoritative status application,
  serialization, expiry/removal contract, and make only a minimal correction if
  the published snapshot is insufficient.
- **ui-developer:** implement the status-derived battlefield figure effect,
  responsive/effect-layer compatibility, accessibility preservation, and UI
  documentation.
- **test-automator:** add deterministic lifecycle and renderer regression
  coverage, run the specified validation, and report exact results.
- **reviewer:** independently review status authority, stale-state risks,
  formation/layering/interaction regressions, test adequacy, and documentation.

## Completion Notes

Completed 2026-10-15. A living Rogue Comprehensiveness figure now derives
`shadow-evasion-active` and `data-shadow-evasion="active"` solely from the
current snapshot's `status.shadow_evasion`. Only `.figure-art` fades to 50%
opacity (220ms transition), so target controls, selection glow, aura, HP UI,
combat effects, mirroring, and formation depth remain unchanged. The alive
guard prevents a stale visual if a defeated Rogue retains the legacy engine
flag outside the normal round-status path. No engine, mechanics, adapter,
model, API, asset, or targetability change was needed.

Role evidence: `/root/ui029_pm` completed the moderate-risk lifecycle and
five-role gate; `/root/ui029_engine` verified application/expiry/adapter
serialization with no contract gap; `/root/ui029_ui` implemented the
figure-only state and documentation; `/root/ui027_test` added lifecycle and
renderer regression coverage; `/root/ui028_final_reviewer` approved the final
authority, stale-state, layering, interaction, documentation, and
owner-file-preservation review.

Validation: the focused backend lifecycle/API/adapter suite passed **91**
tests (one existing Starlette/httpx deprecation warning); frontend UI-029,
battle screen/status/formation suites passed **77** tests; Python compilation,
content check, TypeScript typecheck, quiet lint, production build, and
`git diff --check` passed. Browser verification at desktop **1597×822** used a
live Debug 1v1 Rogue cast: artwork reported opacity `0.5` while the snapshot
status was active, then `1` after Round 2's authoritative expiry. At narrow
**600×900**, the restored figure and target control remained present with no
horizontal overflow. The Debug interaction was not manually repeated for an
enemy Rogue or a live 2v2/3v3 cast in this session; those boundaries are
covered deterministically by the focused frontend tests rather than claimed as
manual observation.

Documentation: `WEB_UI_ARCHITECTURE.md` and `Style_Guide.md` now describe the
snapshot-owned, artwork-only treatment. `BATTLE_DATA_CONTRACT_V1.md`,
`PYTHON_ADAPTER_API.md`, `Technical/Architecture.md`, `GDD/Combat_System.md`,
and `Screen_Flow.md` need no update because the existing status contract and
combat/route rules are unchanged.

## Pre-implementation role gate — 2026-10-15

**Assessment:** Moderate cross-boundary status-presentation work. The requested
opacity is visually small, but it consumes an authoritative engine status
through adapter serialization and the typed battle snapshot; a shortcut can
create stale figure state or impair targeting/effect layers. All five
configured roles are selected and dispatched. Inspection confirms
`status.shadow_evasion` is already serialized from the engine flag and duration,
so backend work is verification-only unless deterministic lifecycle tests expose
a contract gap. Implementation must derive the state from the current
`CombatantState.statuses` and `hero.alive`, apply opacity only to battlefield
figure artwork, and must not add timers, logs, duration inference, or mechanic
changes.

- **project-manager — `/root/ui029_pm` (dispatched):** lifecycle/dependency
  mapping, scope control, staged gates, documentation decision, and completion
  evidence.
- **game-engine-developer — `/root/ui029_engine` (dispatched):** authoritative
  application/expiry/removal and adapter snapshot verification; backend edits
  require a demonstrated contract failure.
- **ui-developer — `/root/ui029_ui` (dispatched):** status-derived
  figure-only presentation, transitions, formation/effect/target/accessibility
  compatibility, and applicable UI documentation.
- **test-automator — `/root/ui027_test` (dispatched):** deterministic lifecycle
  and renderer regressions plus complete validation evidence.
- **reviewer — `/root/ui028_final_reviewer` (dispatched):** independent final
  review of authority, stale-state, layering/interaction, tests, documentation,
  and owner-file preservation.

**Decision gates:** Engine/adapter verification precedes UI implementation;
focused lifecycle and renderer validation precede desktop/narrow manual checks;
independent reviewer approval precedes completion documentation. If a normal
expiry/removal snapshot retains the stable status ID, UI work stops for the
minimal engine/adapter correction. If only a defeated hero retains it, the
presentation remains `hero.alive`-gated rather than broadening generic status
cleanup. Contract/API/GDD documents require no change if the existing status
snapshot remains sufficient; the final record must state that conclusion.
