# Current Task

**Status:** Ready for Core Team

**Task:** BATTLE-TRANSPARENCY-003 — Complete Published Warrior Roster

**Owner request date:** 2026-09-16

## Objective

Extend Battle Information Transparency to every active skill of every Warrior
specialization in the current published roster:

| Definition | Specialization | Active skills |
| --- | --- | --- |
| `hero.warrior.defence` | Defence | Devastate, Shield Bash, Thunder Pot |
| `hero.warrior.weapon_master` | Weapon Master | Fatal Strike, Armor Crush, Antivenom Potion |
| `hero.warrior.berserker` | Berserker | Moon Slash, Warlust, Strike of Meteorite |

Before the player confirms a Warrior action, provide truthful, compact,
authoritative information about immediate damage/healing and the material
status/control effects that can change the decision. This includes targetless
self actions through an appropriate self-preview; it must not leave Antivenom
Potion or Warlust without Battle Information Transparency.

## Background

BATTLE-TRANSPARENCY-001 and -002 created a finite, engine-owned,
non-mutating, revision-bound preview contract for Mage, Rogue, Priest
Comprehensiveness, and Paladin Retribution. It already supports typed primary
facts for `damage`, `healing`, and `prevented`, with separately typed material
consequences.

Warrior skills introduce front-row melee legality, multi-target actions,
cooldowns, stack/refresh boundaries, damage reductions, healing reduction,
self healing/buffs, control immunity, and possible later DoT effects. The
implementation must audit current live code before exposing each fact. React
must only display server-authored facts; it must not reconstruct Warrior rules.

`Warrior_Comprehensiveness` is a legacy Python class but is not one of the
published, adapter-supported Warrior definitions in `docs/GDD/Hero_System.md`.
It is not part of this task.

## Player Experience

### General presentation

- Targeted skills use the established selected-skill plus legal-target
  hover/focus preview. Damage shows `Damage`, direct-evasion `Hit Chance`, and
  `Target HP`; healing shows `Healing` and `Target HP`, without Hit Chance.
- Multi-target skills may show a one-target draft preview while the player is
  choosing required targets, then authoritative per-target facts for the full,
  distinct legal set. Do not show an aggregate total or relax actual command
  cardinality.
- Targetless self actions must expose a compact self-preview on the selected
  skill/acting-hero area before confirmation. It must not require fake target
  selection or cover battlefield figures. Use the same revision, availability,
  stale-clear, keyboard, touch, and compact-layout safeguards as target preview.
- Show a separate short effect row only for a material current-state outcome.
  Do not expose raw formula inputs, calculate future DoT totals, or imply a
  refresh, stack, control, dispel, or status application that live code does
  not perform.
- `Preview unavailable` is preferable to invented precision and never blocks a
  legal command.

### Required Warrior facts

The engine audit must confirm the exact range and live effect semantics before
the final player wording. The following defines the required decision-relevant
coverage, not permission to alter mechanics.

| Hero / skill | Required preview facts |
| --- | --- |
| Defence — Devastate | Immediate direct damage, Hit Chance, target HP, and the current Armor Breaker application/stack/refresh outcome when material. |
| Defence — Shield Bash | Immediate direct damage, Hit Chance, target HP, Stun/control outcome and its current cooldown consequence where applicable. Handle casting interruption/control immunity only as live code supports; do not claim a guaranteed result where a rule prevents it. |
| Defence — Thunder Pot | Per-target immediate direct damage, Hit Chance, target HP, and material Scoff/control result per selected opponent; self-side Shield Lash/resistance and cooldown facts when current live execution makes them material. Never aggregate pair damage. |
| Weapon Master — Fatal Strike | Immediate direct damage, Hit Chance, target HP, and the current Healing Reduction application/refresh/active boundary with its player-facing percentage only when live state makes it material. |
| Weapon Master — Armor Crush | Immediate direct damage, Hit Chance, target HP, Armor Breaker stack/refresh result, and material Wound/Bleeding status outcome. Do not show later bleeding damage. |
| Weapon Master — Antivenom Potion | Targetless self-preview with authoritative immediate Healing and meaningful current self outcomes such as supported poison/bleed removal, poison-resistance effect, and cooldown. Do not fabricate a target or promise removal of statuses the live action cannot remove. |
| Berserker — Moon Slash | Draft/full per-target immediate direct damage, Hit Chance, target HP, and material Bleeding Moon Slash application boundary. Do not show future bleed damage or total multi-target damage. |
| Berserker — Warlust | Targetless self-preview with the live Warlust state/stack/refresh effect, any immediately material self consequence, and cooldown if live action creates one. Exclude conditional later Blood Frenzy outcomes unless the current action makes an exact immediate fact truthful. |
| Berserker — Strike of Meteorite | Immediate direct damage, Hit Chance, target HP, and material interrupt/control/status outcome only as supported by the audited live path. |

## Engine and Contract Requirements

- Audit all nine live skill paths, their independent effects, target rules,
  cooldown lifecycle, status manager interactions, control/immunity paths, and
  adapter event/serialization support before implementation. Record the audit
  and unresolved legacy-rule ambiguities in a dated analysis document.
- Retain the engine-owned, read-only preview boundary. It must not call
  `Skill.execute`, dry-run/clones, install/consume session/global RNG, mutate
  hero/game/status/stack/duration/cooldown/HP/events/log/turn/revision, or
  create command results.
- Add small audited pure outcome primitives only where they share or
  demonstrably mirror the live path. Preserve current live rules exactly. If
  the audit finds a discrepancy between formula, status lifecycle, adapter
  event, and player-facing rule, record and escalate it rather than silently
  correcting it in preview code.
- Extend the additive preview contract as needed for typed self previews and
  finite Warrior-specific material consequences. Keep existing Mage/Rogue/
  Priest/Paladin preview consumers compatible. Do not add generic arbitrary
  status serialization or full-roster fallback.
- Validate the active revision, actor, available audited skill, legal target
  side/IDs/liveness, exact target cardinality, duplicates, self-action target
  shape, and session lock. Draft selection is permitted only for audited
  multi-target Warrior skills and must not change command requirements.

## Frontend Requirements

- Extend the finite audited skill allowlist for exactly these nine skills and
  consume all Warrior facts through typed provider data only.
- Render current primary damage/healing/prevention and typed effect rows in the
  existing target card and compact dock. Add a restrained acting-hero/skill
  self-preview treatment for Antivenom Potion and Warlust, with no fake target
  cursor, extra battle target control, or visual redesign.
- Clearly identify which combatant receives any non-target effect. Preserve
  existing labels, pointer/keyboard/touch target selection, multi-target
  selection state, stale cancellation, preview accessibility association,
  formation, responsive constraints, command submission, and AUDIO-002 cues.
- Do not calculate range, status/cap/cooldown/stack/control/immunity, legality,
  or Hit Chance in TypeScript.

## Out of Scope

- `Warrior_Comprehensiveness`, every other faculty, future general self-preview
  fallback, full status encyclopedia, later DoT/bleed totals, chained effects,
  summons, generic proc simulation, and any unapproved skill.
- Changes to damage/healing/status/control/immunity/cooldown/formation rules,
  available roster, target rules, game balance, battle events/order, API
  commands, save data, or progression.
- Client-side formula copying, next-RNG-roll prediction, aggregate multi-target
  totals, raw internal formula displays, unrelated UI redesign, or sound work.

## Relevant Files

- `heroes/warrior.py`, `skills/skill.py`, `heroes/hero.py`, and
  `game/status_effect_manager.py` — live rules, targeting, receipts, status,
  cooldown, and lifecycle audit.
- `battle_api/adapter.py`, `battle_api/models.py`, and `battle_api/app.py` —
  authoritative preview validation/evaluation and additive transport.
- `web-ui/lib/battle/types.ts`, `liveProvider.ts`, and `useBattlePreview.ts` —
  typed client and finite allowlist.
- `web-ui/components/battle/BattleScreen.tsx`, supporting skill components,
  and `web-ui/app/globals.css` — target and targetless self-preview treatment.
- `tests/test_battle_transparency_preview.py`,
  `tests/test_battle_transparency_002_preview.py`, new Warrior preview tests,
  and `web-ui/tests/battle-transparency*.test.tsx` — deterministic engine/API/
  UI and regression evidence.
- `docs/GDD/Hero_System.md`, `docs/GDD/Combat_System.md`,
  `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`, `PYTHON_ADAPTER_API.md`,
  `WEB_UI_ARCHITECTURE.md`, `Style_Guide.md`, `docs/Technical/Architecture.md`,
  `docs/Codex/Analysis/`, and `docs/Codex/Completed.md`.

## Acceptance Criteria

1. All nine active skills of the three published Warrior specializations have
   truthful pre-confirmation Transparency coverage.
2. Targeted Warrior skills show authoritative per-target facts; Antivenom
   Potion and Warlust show a useful, non-targeted self-preview.
3. Material Warrior statuses, control, stacks, refreshes, cooldowns, and
   self-side effects appear only when the current audited live state supports
   them. Future DoT/bleed totals and fabricated guarantees do not appear.
4. Multi-target Warrior previews support lawful draft/full selection without
   aggregate totals or changed real command cardinality.
5. Existing preview scope and frontend behavior remain compatible, including
   Mage/Rogue/Priest/Paladin skills, command flow, event ordering, audio,
   formations, responsive layout, and accessibility.
6. Preview is demonstrably non-mutating and RNG-free, and a same-seed command
   after preview matches an untouched control.
7. Contract, API, architecture, style, GDD/technical documentation where
   applicable, analysis, and completion evidence accurately describe the
   audited Warrior scope and any deferred/ambiguous rule.

## Validation Required

- Add focused engine/adapter/API tests for each Warrior skill across direct
  range, evasion, prevention, resistance/defence, target legality, targetless
  shape, cooldown, stack/refresh boundaries, control immunity, self effects,
  multi-target draft/full selection, and later-effect exclusion.
- Prove no state/RNG mutation by deep comparison and failing random helpers;
  prove a same-seed command outcome remains equal to an untouched control.
- Test stale revision/actor, unavailable/out-of-scope skill, dead/wrong-side/
  duplicate target, insufficient/extra multi-target selections, and compatibility
  for every prior Transparency skill/contract.
- Add frontend tests for all primary labels, target/self preview modes, typed
  consequence wording, draft/full multi-target behavior, keyboard/pointer/
  touch, stale/error/compact presentation, no client formula duplication, and
  unchanged command/target/audio behavior.
- Run focused backend/frontend suites, broader relevant adapter/Warrior/status
  regressions, typecheck, lint, production build, py_compile, and diff check.
  Manually validate 1v1, 2v2, and 3v3 Warrior turns including front/rear
  screening, a multi-target pair, targetless actions, status boundaries, and
  control immunity. Record exact results and browser limitations honestly.

## Agent Assignments

**Complexity/risk assessment:** High. This expands a live engine-owned
information feature across nine legacy, status-heavy Warrior actions with
multi-target and targetless paths, control/immunity rules, cooldowns, and a
new self-preview UI boundary. All five roles are required.

- **project-manager:** own audit-to-build sequencing, roster/scope guardrails,
  role dispatch, cross-boundary decisions, documents, and completion evidence.
- **game-engine-developer:** own live-rule audit, pure range/outcome primitives,
  no-mutation/RNG guarantees, adapter/API contract, and backend regression tests.
- **ui-developer:** own typed target/self presentation, accessibility,
  responsive/compact behavior, and frontend documentation.
- **test-automator:** own deterministic Warrior state matrix, contract,
  no-mutation/RNG, interaction, compatibility, and regression coverage.
- **reviewer:** independently assess all rule/status/control truth, scope,
  contract compatibility, UI clarity, validation, and documentation.

## Completion Notes

Pending implementation, validation, and independent review.
