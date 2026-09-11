# Current Task

**Status:** Completed
**Task ID:** BATTLE-TRANSPARENCY-001
**Title:** Battle Information Transparency MVP — Mage and Rogue Damage Skills
**Prepared:** 2026-09-11

## Objective

Implement the first safe version of **Battle Information Transparency**. When a player selects an in-scope damage skill and hovers or keyboard-focuses a legal target before confirming the action, show a compact, authoritative preview of the immediate decision-relevant result.

The MVP applies only to:

| Hero | Included skills |
|---|---|
| Mage Comprehensiveness | Fireball, Arcane Missiles, Frost Bolt |
| Rogue Comprehensiveness | Sharp Blade, Poisoned Dagger |

Rogue Shadow Evasion is a self/targetless buff and is explicitly not part of this target-preview MVP. Healing, other heroes, chained effects, and future damage-over-time totals are deferred.

## Owner Decisions Incorporated

- Start with Mage and Rogue only; all three Mage skills are direct-damage skills and Rogue’s two targetable damage skills are in scope.
- The direct **Hit Chance** field applies only to the skill’s immediate direct damage. It must not include Bleed or Poison application chance.
- A separate effect row may state a conditional material effect, such as `Bleed: 50% chance` or `Poison: 85% chance`.
- Do not show, estimate, or imply future Bleed/Poison tick damage in this MVP.
- Complex/chained skill presentation is deferred; do not add generic “additional effects may occur” behaviour to cover out-of-scope heroes.

## Background

The approved `STUDY-001` report established that React must not calculate combat outcomes and that existing mutating skill execution must not be dry-run for hover previews. Current resolution can consume seeded RNG and mutate HP, statuses, cooldowns, logs, turn state, and secondary targets.

This MVP must therefore use an engine-owned, non-mutating evaluator for a small audited skill allowlist and an additive, revision-bound adapter contract. The UI displays only supplied preview facts. It does not parse descriptions, reconstruct formulas, infer status rules, or calculate damage/hit chance itself.

## Required Player Experience

### Compact target preview

After a player selects an in-scope skill and hovers/focuses a legal target, show a compact panel associated with that target. Use plain, decision-focused labels, for example:

```text
FIREBALL → Venombane
Damage:      18–29
Hit Chance:     85%
Target HP:    21 / 85
```

For Rogue effects, show a separate material-effect row only when it is meaningful:

```text
SHARP BLADE → Venombane
Damage:      12–19
Hit Chance:     85%
Target HP:    21 / 85
Bleed:          50% chance
```

```text
POISONED DAGGER → Venombane
Damage:       6–10
Hit Chance:     85%
Target HP:    21 / 85
Poison:         85% chance
```

- Damage must be the authoritative immediate target-specific range for the live current battle state, including only the same direct-damage adjustments that the audited live path applies. It must not include future DoT, chained, shared, or speculative effects.
- `Hit Chance` means the authoritative probability that the direct damage is not evaded for this target under the current direct-damage resolution rule. It must never include random damage variation, Bleed/Poison chance, or a future unimplemented Accuracy system.
- If the selected direct attack is deterministically prevented/immune under the current target state, show a clear blocked/prevented outcome and `Damage: 0`; do not present a misleading positive damage range or fold prevention into Hit Chance.
- If a fact cannot be supported truthfully for an in-scope situation, show a concise `Preview unavailable` state rather than invented precision. It must not block a legal action.
- Retain current target highlights and selection behaviour. The preview is information only; it does not select, lock, or submit a target.

### Skill-specific content rules

- **Fireball:** immediate direct fire-damage range and direct Hit Chance only.
- **Arcane Missiles:** immediate per-target arcane-damage range and direct Hit Chance only. Do not show aggregate total damage or pretend each target’s random result is independent when the current implementation shares variation.
  - While selecting targets, clearly indicate required target count and show a hovered target’s individual preview only when it can be evaluated truthfully.
  - Once two legal targets are selected, evaluate the complete selected pair for the command-consistent preview; show per-target facts, not a fabricated aggregate.
- **Frost Bolt:** immediate direct frost-damage range and direct Hit Chance. If Cold is not active and can be applied by a successful direct hit, show a concise material consequence such as `On hit: Applies Cold`; if Cold is already active, accurately omit or state that no new Cold application occurs according to the actual rule.
- **Sharp Blade:** immediate direct physical-damage range and direct Hit Chance. Show `Bleed: 50% chance` only when the target can meaningfully receive the Bleed under current status/cap rules; do not show future Bleed damage.
- **Poisoned Dagger:** immediate direct physical-damage range and direct Hit Chance. Show `Poison: 85% chance` only when the target can meaningfully receive/add Poison under current status/stack-cap rules; when the cap/current state prevents a new material Poison effect, do not imply an additional stack or future damage.

### Interaction, accessibility, and responsive rules

- Pointer hover and keyboard focus on the same legal target must request/display the same preview. The target remains the interactive control; the preview must use `pointer-events: none` and must not obstruct target hit areas.
- Clear or ignore a preview when the actor, selected skill, target set, legal actions, or battle revision changes; when playback/auto battle disables commands; or when the skill is unavailable, passive, targetless, or out of scope.
- Use cancellation/debouncing and revision/actor/skill/target matching so rapid target movement cannot display stale information. A stale/error response must be discarded and must not affect command state.
- For touch and compact landscape layouts, use a stable pinned/reserved presentation after a legal target interaction rather than an overlapping popover that hides combatants. Preserve the existing portrait-orientation guard and UI-024 responsive presentation boundaries.
- Provide an accessible association from the focused target to the preview without repeated noisy announcements while a pointer moves. Keep keyboard target selection and Enter/Space behaviour unchanged.

## Engine and Contract Requirements

### 1. Authoritative non-mutating evaluator

- Do not execute existing mutating skill callbacks as a preview and do not clone/restore a live battle to simulate one.
- Introduce a small engine-owned preview/evaluation boundary for only the five approved skills. It must use audited pure outcome/range primitives shared with, or demonstrably equivalent to, the live direct-damage calculation path.
- The evaluator must not call or consume `random.randint`, `random.random`, `choice`, `sample`, or `shuffle`; it must not mutate any hero/game/session field, status, stack, duration, cooldown, log, event cursor, command result, turn state, adapter revision, or RNG state.
- Preserve current live game mechanics exactly. If a skill’s live path has a legacy metadata/formation behaviour, the preview must represent the live outcome rather than silently “correcting” balance. Any discovered inconsistency requiring a rules change must be documented and escalated, not changed inside this task.
- Calculate evasion/direct Hit Chance from the same current authoritative direct-damage rule. Do not implement or infer a global Accuracy stat/model.

### 2. Revision-bound adapter operation

- Add one minimal additive adapter/API operation for previewing a requested action against a live battle revision. It must validate battle existence, expected revision, active actor, selected available in-scope skill, legal target side/IDs, target count, duplicate targets, and complete multi-target selection where required.
- The operation must take the same session-lock/authority boundary as a command but leave the session unchanged. It must never enqueue combat events or advance a turn.
- The typed response must include the echoed revision, actor, skill, requested/selected target IDs, coverage/availability state, per-target current/max HP, immediate primary range or prevented state, direct Hit Chance/reliability fact where authoritative, and material consequences with separate chance/certainty.
- Keep the contract additive and document it in Python and TypeScript. No current battle endpoint, command schema, snapshot, event ordering, or existing caller may break.
- Do not include raw hidden formula inputs or arbitrary internal status names in player-facing data. Use stable typed IDs/fields and map final player copy in an approved presentation layer.

### 3. Frontend integration

- Add a provider/client method that requests the authoritative preview only for the selected in-scope skill and legal hovered/focused target state.
- Render the supplied facts in Battle Screen presentation only. TypeScript must not calculate range, direct Hit Chance, effect chance, cap, resistance, prevention, or target legality.
- Preserve all current player command submission, auto battle, target selection, formation/depth, HUD, presentation queue, and 1920×1080 baseline behaviour outside the new compact preview.

## Out of Scope

- Healing previews, Shadow Evasion, all non-Mage/Rogue skills, all other faculties, future DoT totals, chains, spreads, summons, multi-stage resolution totals, and non-approved status outcomes.
- Adding/changing Accuracy, Evasion, damage, healing, status, immunity, cooldown, targeting, formation, or balance rules.
- A broad skill-system rewrite, full combat simulator, client-side formula copy, prediction from the next seeded random roll, or revealing all internal math.
- Changes to current battle commands, event stream/order, random determinism, stage/Arena progression, or player save data.

## Relevant Files

- `heroes/mage.py` and `heroes/rogue.py` — audit the five in-scope skill formulas/effects and share pure direct-outcome primitives with live paths where safe.
- `heroes/hero.py` and `skills/skill.py` — authoritative direct-damage, evasion, immunity/prevention, formation, and mutation boundaries; preserve existing rules.
- `battle_api/adapter.py`, `battle_api/app.py`, and applicable API models — revision-bound preview validation and additive transport.
- `web-ui/lib/battle/types.ts`, provider/API client modules, and `web-ui/components/battle/BattleScreen.tsx` — typed preview consumption, request lifecycle, hover/focus/pinned interaction, and rendering.
- `web-ui/app/globals.css` and `docs/web-ui/Style_Guide.md` — compact visual/accessibility/responsive treatment.
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`, `docs/web-ui/PYTHON_ADAPTER_API.md`, and `docs/Technical/Architecture.md` — authoritative preview contract/architecture documentation.
- Existing adapter, skill, hero, Battle Screen, quick-targeting, formation, and responsive test suites; add focused preview tests in clear backend/frontend test modules.
- `docs/Codex/Analysis/2026-09-11_Battle_Information_Transparency_Feasibility_Study.md` — approved research basis and scope guardrail.
- `docs/Codex/Completed.md` — completion evidence and actual role contributions.

## Acceptance Criteria

1. Hovering/focusing a legal target with each in-scope selected skill shows an authoritative compact target preview before command confirmation.
2. Fireball, Arcane Missiles, Frost Bolt, Sharp Blade, and Poisoned Dagger show only truthful immediate direct-damage information for the current target/state.
3. `Hit Chance` applies only to direct damage and is separate from random damage range and status-proc chance.
4. Sharp Blade shows a separate 50% Bleed chance only when meaningful; Poisoned Dagger shows a separate 85% Poison chance only when a material application/addition is possible. Neither shows future DoT damage.
5. Frost Bolt accurately communicates its immediate Cold consequence only when the current rule supports it; Arcane Missiles handles two-target selection without a fake aggregate total.
6. Preview requests/responses make no combat, UI command-state, session, event, revision, or RNG mutation. A command after preview remains identical in seeded outcome to the same command without preview.
7. The backend rejects invalid/stale/out-of-scope preview requests safely and without mutation; the UI clears/discards stale data without blocking a legal command.
8. The UI is usable by pointer, keyboard, and compact/touch layout without blocking target hit areas or changing existing target selection/highlight behaviour.
9. Existing commands, combat results, API consumers, UI-024 responsive presentation, and 1920×1080 baseline remain unchanged outside the compact preview.
10. Contract, architecture, style guidance, and completion documentation describe the actual approved MVP scope and do not imply unsupported full-roster coverage.

## Validation Required

- Add backend unit/integration tests for each in-scope skill across minimum/maximum direct range, direct Hit Chance/evasion, deterministic prevention/immune state, current status/stack boundaries, and exact Arcane Missiles pair behaviour.
- Prove preview has no state or RNG impact: deep-compare relevant game/session/snapshot data and random/session RNG state before/after preview; patch all random helpers to fail during preview; prove the later same-seed command result matches an untouched control.
- Test stale revision, inactive actor, unavailable/out-of-scope skill, wrong side, dead target, duplicate target, insufficient/extra Arcane target selection, and rapid request cancellation/error behaviour.
- Add frontend tests for pointer hover, keyboard focus, target selection, stale/error clearing, in-scope/out-of-scope visibility, separate effect-proc wording, prevented state, Arcane multi-target presentation, responsive/touch pinned state, and no client formula duplication.
- Run relevant Python, API, frontend, typecheck, lint/build as applicable, and `git diff --check`.
- Manually validate 1v1, 2v2, and 3v3 with Mage/Rogue player turns, including formations with screened melee targets, evasion/prevention state, Rogue status stack boundaries, and compact responsive viewport.
- Record exact validation commands/results, any unsupported edge cases, and actual agent contributions in `Completed.md`.

## Agent Selection and Dispatch Gate

**Complexity/risk assessment:** High cross-system implementation. It adds a new authoritative game-information capability spanning legacy stateful combat calculation, RNG guarantees, adapter/API contract validation, asynchronous frontend interaction, responsive/accessibility presentation, and misleading-information risk. All five roles are required.

**Selected roles — must be concretely dispatched before implementation:**

- **project-manager:** coordinate the study-to-build handoff, phased dependency order, agent dispatch, scope guardrails, documentation, and evidence.
- **game-engine-developer:** own audited pure evaluator/primitives, no-mutation/RNG guarantees, adapter/API validation, and additive typed contract.
- **ui-developer:** own provider request lifecycle, Battle Screen target-preview presentation, accessibility, and responsive compact/touch behaviour.
- **test-automator:** own deterministic backend/frontend contract, no-mutation/no-RNG, stale/legality, interaction, and regression coverage.
- **reviewer:** independently assess range/hit/proc truthfulness, authority boundaries, random determinism, UI clarity, contract compatibility, and scope compliance.

## Completion Notes

Implemented and independently reviewed on 2026-09-11. The authoritative
completion evidence, dispatch contributions, validation, and deferred scope are
recorded in `docs/Codex/Completed.md`.
