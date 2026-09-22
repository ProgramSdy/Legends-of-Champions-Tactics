# BATTLE-TRANSPARENCY-004 — Paladin Holy and Protection

**Queue state:** Owner-approved next task. Do not start implementation until
`BATTLE-TRANSPARENCY-003 — Complete Published Warrior Roster` is completed
and this brief has been promoted into `docs/Codex/Current_Task.md`.

**Owner request date:** 2026-09-18

## Objective

Extend Battle Information Transparency to every **player-selectable active
skill** of the published Paladin Holy and Paladin Protection specializations.
Before a player confirms an action, show compact, truthful, server-authored
facts about its immediate damage or healing and the material current-state
effects that influence that decision.

The scope is six active skills:

| Hero | Active skills |
| --- | --- |
| Paladin Protection | Hammer of Revenge, Shield of Righteous, Heroric Charge |
| Paladin Holy | Purify Healing, Holy Blast, Shield of Protection |

`Holy Aura` is a passive, round-start effect rather than a player-selectable
action. It must not receive a click/target preview in this task.

## Background

The existing engine-owned preview system already covers Mage, Rogue, Priest
Comprehensiveness, and Paladin Retribution. It is revision-bound, typed,
non-mutating, and RNG-free. React requests and displays facts; it does not
execute a skill or recreate combat calculations.

The immediately preceding Warrior task introduces the shared targetless
`selfPreview` boundary for actions such as Warlust and Antivenom Potion. This
Paladin task must reuse that completed boundary rather than introduce a second
self-preview shape. In particular, Holy's Shield of Protection has no target
selection and must not be represented by a fake target.

Paladin skills combine direct attacks with self buffs, dispels, healing,
cooldown, stacking, conditional bonuses, control, and immunity. The live code
must be audited before the final player wording is chosen. A preview must not
silently change or "repair" a legacy game rule.

## Player Experience and Requirements

### Shared presentation rules

- A selected targeted skill shows a compact target preview on legal
  hover/focus. Direct damage shows `Damage`, direct-evasion `Hit Chance`, and
  `Target HP`. Healing shows `Healing` and `Target HP`, with no Hit Chance.
- A quantity-two skill may show a per-target draft while targets are being
  selected and per-target facts for the complete legal pair. Do not display an
  aggregate total or change the real command's target cardinality.
- Targetless Shield of Protection uses the established compact self-preview on
  the selected skill/acting-hero area. It must not cover combat figures,
  require a target, or alter target-selection controls.
- Show a short effect row only where a current, audited outcome materially
  affects the decision. Do not expose raw formulas, promise a later reaction,
  or calculate future DoT totals.
- If a fact cannot be proven from the live implementation, show `Preview
  unavailable` or omit that row. A preview never blocks a legal action.

### Required audited coverage

| Hero / skill | Required preview information |
| --- | --- |
| Protection — Hammer of Revenge | Immediate direct damage, Hit Chance, Target HP, and its current self-debuff damage-band result. When Shield of Righteous makes the target damage-reduction effect applicable, show the precise current application/refresh result only if the live path supports it. |
| Protection — Shield of Righteous | Immediate direct melee damage, Hit Chance, Target HP, and the actor's defence-buff application, stack, cap, or duration-refresh result. Do not promise the 100% buff result without auditing the actual live path. |
| Protection — Heroric Charge | Immediate direct damage, Hit Chance, Target HP, and only the current auditable control/interrupt, Scoff, self-healing, and cooldown outcomes. Respect target control immunity and active magic-casting state; do not present an interruption where it cannot occur. |
| Holy — Purify Healing | Immediate healing range and target HP, with no Hit Chance; show the current Purify Healing buff application/refresh and at most the one eligible debuff removal that the live dispeller can actually choose. Do not reveal or predict which eligible status RNG will select if more than one exists. |
| Holy — Holy Blast | Immediate direct damage, Hit Chance, and Target HP for each selected enemy. Show the existing first-target versus later-target difference only as authoritative per-target ranges, never an aggregate. |
| Holy — Shield of Protection | Targetless self-preview with the current damage-immunity application/refresh, any eligible debuffs actually removed by the live action, and the live cooldown result. Do not claim future blocked attacks, draw a fake target, or forecast damage that a later attacker might deal. |

## Engine and Contract Requirements

- Before implementation, perform and record a dated audit of all six live
  skill functions, their `independent_effect_action` paths, target rules,
  formation/receipt handling, status manager and dispeller behaviour,
  cooldown lifecycle, stacking/refresh boundaries, control/immunity, and
  adapter serialization. Record unresolved legacy ambiguity rather than
  approximating it.
- Preserve existing live mechanics exactly. Add small, named pure primitives
  only when they share or demonstrably mirror the audited immediate live path.
  Pure preview evaluation must never call `Skill.execute`, callbacks,
  `resolve_targets`, `_resolve`, status update, or live random helpers.
- Keep preview engine-owned and held under the revision/session lock. Validate
  revision, current actor, audited available skill, lawful side/ID/liveness,
  duplicates, exact target count, and targetless action shape.
- Reuse BATTLE-TRANSPARENCY-003's additive `selfPreview` contract for Shield
  of Protection. Keep all established targeted preview consumers compatible.
  Any new consequence types must be finite, typed, recipient-specific, and
  documented; do not serialize arbitrary status dictionaries.
- Do not consume session or process RNG, or mutate HP, stats, status maps,
  buffs/debuffs, stacks, durations, cooldowns, events/logs/cursors, command
  results, turns, revision, or RNG state. Same-seed gameplay after preview
  must match an untouched control.

## Frontend Requirements

- Extend the finite preview allowlist for exactly the six active skills after
  confirming their published IDs. Do not enable the passive Holy Aura or a
  generic Paladin fallback.
- Use typed provider facts only. Render damage/healing/prevention and finite
  consequence rows in the existing target card/compact dock, and reuse the
  finished targetless self-preview treatment for Shield of Protection.
- For Purify Healing, make removal wording honest about uncertainty: show only
  a supported "removes one eligible …" style row when the engine audit confirms
  multiple eligible statuses can be randomly chosen; never label one particular
  status as guaranteed unless it is the sole eligible live choice.
- Preserve pointer, focus, keyboard, touch, stale/abort, accessibility,
  formation, responsive layout, command flow, and AUDIO-002 behaviours. No
  TypeScript combat calculations or UI redesign.

## Out of Scope

- Holy Aura passive preview, Paladin Retribution changes, every other class,
  generic all-roster preview, balance/rule changes, passive tooltip redesign,
  later damage prevention forecasts, future DoT totals, chained effects,
  generic proc simulation, raw formula displays, API command changes, or
  sound/VFX work.
- Any duplicate/competing targetless-preview contract. If the preceding
  Warrior task's contract needs a material correction, resolve that task first
  and reuse its final agreed boundary here.

## Relevant Files

- `heroes/paladin.py`, `heroes/hero.py`, `skills/skill.py`, and
  `game/status_dispell.py` / status services — source mechanics and audit.
- `battle_api/adapter.py`, `battle_api/models.py`, `battle_api/app.py` —
  authoritative validation, pure evaluation, and additive endpoint.
- `web-ui/lib/battle/types.ts`, `liveProvider.ts`, `useBattlePreview.ts`,
  `web-ui/components/battle/BattleScreen.tsx`, and `web-ui/app/globals.css` —
  typed transport and presentation.
- Existing and new Transparency backend/API/frontend tests.
- `docs/GDD/Hero_System.md`, `docs/GDD/Combat_System.md`,
  `docs/Technical/Architecture.md`, `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`,
  `docs/web-ui/PYTHON_ADAPTER_API.md`, `docs/web-ui/WEB_UI_ARCHITECTURE.md`,
  `docs/web-ui/Style_Guide.md`, `docs/Codex/Analysis/`,
  `docs/Codex/Current_Task.md`, and `docs/Codex/Completed.md`.

## Acceptance Criteria

1. Every listed active Holy/Protection skill has truthful pre-confirmation
   coverage, while passive Holy Aura remains outside the interaction scope.
2. Targeted actions show authoritative per-target facts, Holy Blast respects
   its exact selected-target sequence, and Shield of Protection has a useful
   targetless self-preview without a fake target.
3. Conditional buffs, stacks, refreshes, dispels, control, immunity, healing,
   and cooldown rows appear only when the audited current live state makes
   them true; uncertain random dispel selection is not falsely specific.
4. The preview stays non-mutating and RNG-free, including success and rejected
   requests, and same-seed commands remain identical to untouched controls.
5. Existing Transparency skills, target selection, commands, status/event
   ordering, audio, formations, accessibility, and responsive presentation
   remain compatible.
6. Contract/API/architecture/style/GDD documentation, dated audit, tests, and
   completion evidence accurately record the implemented scope and deferrals.

## Validation Required

- Add a focused audit-backed backend/API suite for all six skills, direct
  ranges, formation/defence/resistance/receipt, evasion, target legality,
  exact Holy Blast draft/full cardinality, targetless Shield shape, stacks,
  refresh/cap, cooldown, status-control-immunity, dispeller boundaries, and
  unsupported/unavailable cases.
- Deep-compare all relevant state and both RNG sources before/after successful
  and rejected previews; patch random helpers to fail; prove same-seed command
  equivalence against an untouched control.
- Add frontend tests for labels, target/self modes, per-target multi preview,
  uncertainty wording, keyboard/pointer/touch, stale/error/compact behaviour,
  accessibility, no client formula logic, and unchanged command/audio flow.
- Run focused and broader relevant backend/adapter/Paladin/status regressions;
  frontend tests, typecheck, lint, production build, Python compilation, and
  diff check. Manually validate 1v1, 2v2, and 3v3 including screened melee,
  Holy Blast pair selection, Purify status states, Shield of Righteous cap,
  Heroric Charge control paths, and Shield of Protection.

## Agent Assignments

**Complexity/risk:** High. The task crosses legacy Paladin mechanics,
status/dispeller logic, multi-target and targetless previews, adapter contract,
frontend presentation, deterministic safety, and regression scope. Dispatch all
five configured roles after promotion.

- **project-manager:** sequence audit/build/test/review gates, protect scope,
  record role dispatch and completion evidence.
- **game-engine-developer:** audit live behaviour; implement pure primitives,
  adapter/API facts, and no-mutation/RNG guarantees.
- **ui-developer:** own typed target/self presentation, uncertainty wording,
  accessibility, responsive behaviour, and frontend documentation.
- **test-automator:** own deterministic engine/API/UI state matrix, purity,
  contract, interaction, and compatibility coverage.
- **reviewer:** independently verify mechanic truth, scope, contract/UI
  compatibility, documentation, and validation evidence.

## Completion Notes

Pending. Promote this brief only after BATTLE-TRANSPARENCY-003 is complete.
