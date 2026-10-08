# BATTLE-TRANSPARENCY-005 — Priest Discipline

**Queue state:** Owner-approved next task. Do not start implementation until
UI-027 is complete and this brief has been promoted into
`docs/Codex/Current_Task.md`.

**Owner request date:** 2026-10-08

## Objective

Complete Battle Information Transparency for the final approved web hero:
Priest Discipline (`hero.priest.discipline`). Before a player confirms each
available action, show compact, authoritative, decision-relevant immediate
facts without mutating the battle or consuming RNG.

| Skill | Required target shape |
| --- | --- |
| Penance | One selected living ally **or** one legal living opponent |
| Holy Word Redemption | One selected living ally |
| Holy Word Punishment | Two selected legal living opponents, with audited draft support only if lawful |

The task completes Transparency coverage for all ten approved hero
specializations. It does not turn Transparency into a generic preview system.

## Background

BATTLE-TRANSPARENCY-001 through -004 established a finite, engine-owned,
revision-bound, typed, read-only preview path. React requests and renders facts
only; it does not execute skills, calculate combat, infer state, or predict an
RNG roll.

Priest Discipline adds a hybrid action whose result depends on target side,
Redemption-linked secondary healing, and a multi-target damage/debuff action.
Its legacy implementation must be audited before any player-facing wording is
chosen. Existing code appearance alone is not evidence that a result is
hit-gated, serialized, or safe to promise in preview.

## Player Experience and Requirements

### Shared presentation

- Direct damage previews show server-authored `Damage`, direct-evasion `Hit
  Chance`, and `Target HP`. Healing previews show `Healing` and `Target HP`,
  with no Hit Chance.
- The selected Penance action must work correctly for both lawful target sides:
  an ally gets a healing preview; an opponent gets a damage preview. The UI may
  identify the branch plainly, but it must not decide side effects itself.
- Holy Word Punishment may show per-target draft facts while a lawful required
  pair is being selected, then per-target facts for the complete distinct pair.
  Never provide an aggregate total or relax the real command cardinality.
- Material current-state effect rows must be finite, typed, recipient-specific,
  and truthful. Do not expose raw formulas, future DoT totals, an exact future
  random roll, or a generic status dump. `Preview unavailable` is preferable to
  invented precision and never blocks a legal command.

### Required audited coverage

| Skill / selected side | Required preview information |
| --- | --- |
| Penance — ally | Immediate healing range and target HP; any current, audited healing modifier/receipt fact that materially changes the result. No Hit Chance. |
| Penance — opponent | Immediate direct damage range, Hit Chance, Target HP, and the current audited Holy Word Redemption secondary-healing consequence for each actual linked ally. Show recipient-specific immediate facts only; do not aggregate or forecast later actions. |
| Holy Word Redemption | Current target-side application or duration-refresh outcome and only the immediate, auditable player-facing meaning of the buff. Do not claim an exact future heal, generic cooldown rule, or a later Penance/Punishment result the current state cannot prove. |
| Holy Word Punishment | Per selected opponent: immediate direct damage, Hit Chance, Target HP, and current application/already-active/other audited boundary for its debuff. Explicitly exclude future periodic-damage totals. Where live Redemption links create immediate secondary healing, represent each lawful recipient and target-triggered result in a finite typed form only if the audit proves the live ordering/receipt. |

## Engine and Contract Requirements

- First create a dated, source-cited audit covering all three live callbacks,
  target-side resolution, hybrid Penance dispatch, formation and receipt/evasion
  paths, Holy Word Redemption ownership/duration, Punishment application and
  tick lifecycle, secondary-healing order/coefficient, status manager,
  adapter event serialization, target legality, cooldowns, and AI/forced-path
  compatibility. Record any legacy ambiguity or mismatch; do not silently
  repair game mechanics as part of preview work.
- Preserve live mechanics. Add small named pure primitives only where they
  share or demonstrably mirror immediate live behaviour. Preview must never
  call `Skill.execute`, callbacks, `resolve_targets`, adapter `_resolve`,
  status update, or random helpers.
- Validate revision, current actor, audited available skill, target side/ID/
  liveness, target count, duplicates, and Penance's valid side-dependent
  shape under the existing session lock. Keep all prior preview consumers and
  contracts compatible.
- Do not consume session/process RNG or mutate HP, stats, status maps,
  buffs/debuffs, stacks, durations, cooldowns, events/logs/cursors, command
  results, turns, revision, or RNG state. A same-seed command after preview
  must equal an untouched control.
- Extend the finite typed consequence/secondary-recipient contract only where
  necessary. Do not add arbitrary status serialization or a generic fallback.

## Frontend Requirements

- Add exactly these three audited skill IDs to the finite allowlist after
  confirming their published IDs. Do not enable a generic Priest fallback.
- Render typed Penance ally/enemy facts and only server-supplied Redemption
  secondary-recipient facts. The browser must not decide Penance branch,
  compute range/Hit Chance/healing, infer linked allies, or transform a skill
  into a different target shape.
- Reuse existing hover/focus/pinned compact treatment, draft/full multi-target
  interactions, stale/abort identity checks, accessibility associations,
  pointer/keyboard/touch selection, responsive layout, and AUDIO-002 cues.
- Keep target-side language clear and compact. It must not obscure battlefield
  figures, alter command submission, or replay sounds/events.

## Out of Scope

- All non-Discipline heroes/skills, generic all-roster fallback, balance or
  combat-mechanic changes, Priest Discipline unlock/progression work, full
  status encyclopedia, later periodic-damage totals, generic proc simulation,
  raw formula displays, UI redesign, or sound/VFX changes.

## Relevant Files

- `heroes/priest.py`, `heroes/hero.py`, `skills/skill.py`, and status services.
- `battle_api/adapter.py`, `battle_api/models.py`, and `battle_api/app.py`.
- `web-ui/lib/battle/types.ts`, `liveProvider.ts`, `useBattlePreview.ts`,
  `web-ui/components/battle/BattleScreen.tsx`, and `web-ui/app/globals.css`.
- Existing/new Transparency backend/API/frontend tests.
- `docs/GDD/Hero_System.md`, `Skill_System.md`, `Combat_System.md`,
  `docs/Technical/Architecture.md`, web UI data/API/style documents,
  `docs/Codex/Analysis/`, `Current_Task.md`, and `Completed.md`.

## Acceptance Criteria

1. Priest Discipline's three active skills have truthful pre-confirmation
   transparency coverage, completing all ten approved web specializations.
2. Penance accurately distinguishes legal ally-healing from opponent-damage
   previews without client-side combat logic.
3. Redemption and Punishment present only audited immediate application,
   refresh, secondary-healing, and status facts; future periodic damage and
   invented exact outcomes do not appear.
4. Multi-target Punishment retains lawful draft/full selection and no aggregate
   total or altered command shape.
5. Preview purity, RNG safety, all existing scope compatibility, accessibility,
   formation, events, audio, and responsiveness are preserved.
6. Audit, contract/API/architecture/style/GDD documentation where applicable,
   tests, validation evidence, and completion records accurately describe the
   final complete-roster scope and deferrals.

## Validation Required

- Add focused engine/API coverage for all three skills across ally/opponent
  Penance branches, range/receipt/evasion/formation, lawful side/target shape,
  Redemption ownership/application/refresh, Punishment draft/full cardinality,
  status boundary, secondary recipient facts, unavailable/out-of-scope/stale/
  dead/wrong-side/duplicate rejection, and prior-scope compatibility.
- Deep-compare state and both RNG sources before/after accepted and rejected
  previews; patch random helpers to fail; prove same-seed command equivalence.
- Add frontend coverage for side-aware Penance facts, Redemption/Punishment
  typed rows, multi-target selection, stale/error/compact states, keyboard/
  pointer/touch/accessibility, no client formula duplication, and unchanged
  command/audio behaviour.
- Run focused and relevant broader backend/frontend regressions, typecheck,
  lint, production build, Python compilation, diff check, and honest manual
  1v1/2v2/3v3 validation including both Penance branches, Redemption-linked
  state, and Punishment pair selection. Record exact evidence and limitations.

## Agent Assignments

**Complexity/risk:** High. Hybrid side-dependent targeting, multi-target
preview, status lifecycle, linked recipients, engine/API contract, frontend
presentation, deterministic safety, and full-roster completion require all five
configured roles after promotion.

- **project-manager:** audit/build/review sequencing, scope, role dispatch,
  cross-boundary decisions, documentation, and completion evidence.
- **game-engine-developer:** live-rule audit; pure primitives; adapter/API;
  status/secondary-recipient truth; and no-mutation/RNG guarantees.
- **ui-developer:** typed side-aware presentation, compact/accessibility/
  responsive interaction, and frontend documentation.
- **test-automator:** deterministic hybrid/multi/status/purity/compatibility
  matrix and integrated regression coverage.
- **reviewer:** independent mechanic, contract, UI, validation, and document
  review.

## Completion Notes

Pending. Promote only after UI-027 is completed and formally recorded.
