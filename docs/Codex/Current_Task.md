# Current Task

**Status:** Ready for Core Team

**Task:** UI-030 — Hero Gallery Target-Dependent Damage References for Warrior Weapon Master

**Owner request date:** 2026-10-16

## Objective

Extend the existing Hero Gallery skill-reference pattern so every published
skill whose Base Damage is truthfully **Target-dependent** uses the same
presentation already established for Priest Comprehensiveness's Shadow Word
Pain:

- show **Target-dependent** rather than an invented static damage range;
- show the existing yellow `?` calculation trigger beside Base Damage; and
- open the existing accessible calculation popup containing the
  backend-authored player-facing formula.

Complete the next requested Warrior Weapon Master references:

1. **Fatal Strike** — resolve as Target-dependent Base Damage, with its exact
   direct-damage formula in the calculation popup.
2. **Armor Crush** — resolve as Target-dependent Base Damage, including the
   authoritative Armor Breaker stack-dependent direct-damage formula/condition
   bands in the calculation popup.
3. **Antivenom Potion** — add its audited **Base Healing** box for the
   self-heal, while preserving its non-damaging/buff classification and other
   mechanics.

This task only exposes existing mechanics accurately. It does not change live
damage, healing, status, stacks, poison resistance, healing reduction, cooldown,
targeting, RNG, or Warrior balance.

## Background

UI-028 established typed, deterministic, read-only skill-reference metadata
on `GET /api/v1/heroes`. The Gallery already renders an unavailable numeric
reference with `reasonId: "targetDependentBaseline"`, display label
**Target-dependent**, and adapter-authored `calculation` title/text as the
yellow `?` popup. Shadow Word Pain and the two Rogue direct-damage skills are
existing examples.

Warrior Weapon Master's live methods have target-dependent direct damage:

- Fatal Strike uses caster Damage plus variation, less target Defence, with a
  live minimum-damage floor.
- Armor Crush uses caster Damage plus variation and target Defence, then
  applies an Armor Breaker-state multiplier and its live rounding/floor rules.
- Antivenom Potion heals the caster from a fixed base plus variation, while
  separately applying its existing poison-resistance and dispel/buff effects.

The Gallery catalogue must remain static/read-only: it must not instantiate a
hero, execute a skill, create a battle/session, mutate state, or consume RNG.
React only renders typed backend facts; it must not contain a combat formula.

## Requirements

### 1. Reuse the established Target-dependent presentation

- Reuse the existing `SkillReferenceCard`, `buildSkillReferenceRows`, yellow
  calculation trigger, dialog accessibility/close behavior, and compact
  Hero Gallery styling. Do not build a second popup or a new visual pattern.
- For any already-published skill whose authoritative `baseDamage` has
  `reasonId: "targetDependentBaseline"`, ensure the Gallery presents
  **Target-dependent** with the yellow `?` and supplied formula popup exactly
  as Shadow Word Pain does.
- Audit the existing target-dependent inventory rather than blindly changing
  every unavailable damage value. A skill becomes Target-dependent only when
  its live direct formula has an inseparable target-specific input that makes a
  caster-only Base Damage range misleading. Other un-audited skills remain
  truthfully unavailable.
- Formula text, title, display label, reason ID, and conditions are
  adapter-owned typed metadata. The browser must neither reconstruct,
  interpolate, nor calculate formulas.

### 2. Fatal Strike

- Audit the actual live `Warrior_Weapon_Master.fatal_strike` path, including
  variation, target Defence, the minimum-damage floor, receipt path, and the
  healing-reduction status/refresh behavior.
- Publish **Base Damage: Target-dependent** with the existing calculation
  popup. The formula must accurately describe the direct pre-receipt result
  and its live minimum floor, using player-friendly terms such as Caster
  Damage, Skill Variation, and Target Defence.
- Do not state or imply that the popup formula is final damage dealt. Clearly
  separate any material existing healing-reduction effect from the direct
  formula only when its exact current game behaviour is verified. Do not
  invent a percentage, duration, refresh rule, or aggregate effect.

### 3. Armor Crush

- Audit the actual live `Warrior_Weapon_Master.armor_crush` path, including
  variation, target Defence, `ceil`/minimum-floor behavior, Armor Breaker
  absent/one-stack/two-or-more-stack multiplier cases, stack cap/refresh, and
  associated defence/agility/wound/bleeding side effects.
- Publish **Base Damage: Target-dependent** and reuse the calculation popup.
  Its text must make clear which multiplier applies in each verified Armor
  Breaker state and retain the actual rounding/minimum semantics. It must not
  claim a target-independent number, total periodic damage, or a guaranteed
  stack outcome.
- Describe any material status consequences only where already authoritative
  and relevant to the Gallery reference. Keep formulas concise and readable;
  a popup is explanatory reference material, not a full rules worksheet.

### 4. Antivenom Potion

- Audit its current direct self-healing calculation and publish **Base
  Healing: 18–20** only if the audit confirms the existing base value and
  `-1..+1` variation still govern the live heal.
- Label the value as self-healing power before healing modifiers and the HP
  cap. Do not call it damage or expose irrelevant damage classifications.
- Preserve its existing self target, buff identity, poison-resistance change,
  eligible-status dispel behavior, duration, and cooldown. These effects must
  not be changed merely to support the Gallery.

### 5. Authority, compatibility, and scope controls

- Keep the additive frozen v1 Hero Gallery catalogue compatible with existing
  clients and retain exact stable hero/skill IDs.
- Prefer the smallest pure static helper/constants extraction only if required
  to keep Gallery reference text/range proof aligned with live code. Any
  extraction must preserve live arithmetic, rounding, RNG call count/order,
  event/status ordering, and behaviour. No runtime hero construction or RNG is
  allowed for a catalogue read.
- Preserve existing Shadow Word Pain, Rogue Target-dependent popups, current
  skill-card accordion/tabs, YAML editorial content, accessibility, responsive
  facts grid, and all unrelated Gallery references.

## Out of Scope

- Changing Warrior Weapon Master combat formulas, game balance, status rules,
  skill descriptions in YAML unless factual correction is required, cooldowns,
  target legality, healing receipt, battle events, or AI.
- Converting all unavailable damage references into Target-dependent ones
  without a formula audit; sampled/randomized estimates; live Battle
  Information Transparency; frontend combat calculations; a new modal/popup
  design; or a Hero Gallery layout redesign.
- New assets, status effects, audio, backend API version, progress/save work,
  commits, pushes, PRs, or publication without separate owner authorisation.

## Relevant Files

- `heroes/warrior.py` — `Warrior_Weapon_Master.fatal_strike`, `armor_crush`,
  `antivenom_potion`, and existing audited range helpers; live source of truth.
- `heroes/hero.py`, `skills/skill.py`, status/receipt paths, and Warrior
  engine tests — inspect for actual calculation and side-effect ordering.
- `battle_api/adapter.py`, `battle_api/models.py`, `battle_api/app.py`,
  `tests/test_ui028_skill_reference_metadata.py`, and roster/API tests —
  static catalogue reference authority and v1 contract.
- `web-ui/components/manual/HeroGalleryExperience.tsx`,
  `web-ui/lib/manual/heroGalleryPresentation.ts`,
  `web-ui/lib/battle/types.ts`, `web-ui/lib/battle/liveProvider.ts`, Gallery
  CSS, and Gallery presentation tests — existing popup/rendering boundary.
- `web-ui/content/hero-gallery/warrior-weapon-master.yaml` and content
  validation — editable editorial text only; mechanics remain backend-owned.
- `docs/Codex/Analysis/2026-10-10_UI-028_Hero_Gallery_Skill_Reference_Audit.md`,
  `docs/GDD/Skill_System.md`, `docs/Technical/Architecture.md`,
  `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`,
  `docs/web-ui/PYTHON_ADAPTER_API.md`, `docs/web-ui/WEB_UI_ARCHITECTURE.md`,
  and `docs/web-ui/Style_Guide.md`.

## Acceptance Criteria

1. Shadow Word Pain and existing Rogue Target-dependent skill references keep
   their current label, yellow `?`, backend-authored popup, and formula text.
2. Fatal Strike has Base Damage **Target-dependent** and its popup accurately
   explains the audited direct formula, variation, Target Defence, and minimum
   floor without claiming final received damage.
3. Armor Crush has Base Damage **Target-dependent** and its popup accurately
   explains the audited direct formula plus the applicable Armor Breaker
   multiplier states, rounding, and floor without fabricated totals/effects.
4. Antivenom Potion shows Base Healing **18–20** with a truthful self-healing
   explanation; Base Damage and damage classifications remain inapplicable.
5. All published Target-dependent values are based on an explicit authoritative
   formula audit; unrelated un-audited skills remain unavailable.
6. The solution stays deterministic/read-only/RNG-free for catalogue reads;
   React renders server facts without formulas or gameplay calculation.
7. Accordion, tabs, keyboard/pointer dialog behavior, responsive layout,
   content/YAML validation, other Gallery skills, and live combat mechanics
   remain compatible.

## Validation Required

- Add deterministic backend/API tests for Fatal Strike, Armor Crush, and
  Antivenom metadata shape, stable IDs, exact Target-dependent reason/label,
  formula text, all audited multiplier/rounding/floor conditions, Base Healing
  boundary, correct applicability states, and frozen v1 compatibility.
- Prove catalogue reads do not instantiate heroes, execute skills, create
  sessions, mutate state, or consume RNG. If a live/helper extraction occurs,
  add execution-parity and random-call-order tests for representative normal
  and conditional Armor Crush/Fatal Strike/Antivenom cases.
- Add/update frontend tests that open the familiar yellow calculation dialog
  for Fatal Strike and Armor Crush; verify title/formula, close/focus/keyboard
  behavior, no raw enum/formula logic in React, Antivenom Base Healing,
  relevant-field omission, and preserved Shadow Word Pain/Rogue behavior.
- Run content validation, relevant Gallery/API/engine/adapter regressions,
  typecheck, lint, production build, Python compilation, and `git diff
  --check`. Manually inspect Warrior Weapon Master expanded cards on desktop
  and tablet/narrow viewport for readable popup/grid behavior and no clipping.
- Record exact commands/results, audited assumptions, and any value that stays
  unavailable because its formula is not proven.

## Agent Assignments

**Complexity/risk:** Moderate cross-boundary reference work. The requested UI
pattern already exists, but the task exposes legacy target-dependent Warrior
formulas through a public read-only API and must not drift from combat/RNG or
mislead players. All five roles are selected for formula authority,
presentation, deterministic test coverage, and independent review.

- **project-manager:** lead the exact formula audit, scope gate, role
  coordination, documentation, and completion evidence.
- **game-engine-developer:** own live-formula/side-effect audit, static
  catalogue metadata, smallest safe shared-helper work if needed, API contract,
  and engine parity evidence.
- **ui-developer:** reuse the existing target-dependent calculation UI,
  preserve accessibility/responsiveness, and integrate typed presentation
  without client mechanics.
- **test-automator:** own deterministic contract/formula-boundary/parity and
  Gallery dialog/content regression coverage plus integrated validation.
- **reviewer:** independently verify formula truth, scope limits, status/rounding
  conditions, read-only/RNG guarantees, UI reuse/accessibility, and docs.

## Completion Notes

Pending formula audit, implementation, validation, independent review, and
owner-approved publication only.
