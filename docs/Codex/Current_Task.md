# Current Task

**Status:** Completed — 2026-10-08

**Task:** BATTLE-TRANSPARENCY-005 — Priest Discipline

**Owner request date:** 2026-10-08

**Detailed task brief:**
`docs/Codex/Analysis/2026-10-08_BATTLE-TRANSPARENCY-005_Priest_Discipline_Task_Brief.md`

## Objective

Complete Battle Information Transparency for the final approved web hero:
Priest Discipline (`hero.priest.discipline`). Before confirmation, show compact,
authoritative, decision-relevant immediate facts without mutating battle state
or consuming RNG.

| Skill | Target shape |
| --- | --- |
| Penance | One selected living ally **or** one legal living opponent |
| Holy Word Redemption | One selected living ally |
| Holy Word Punishment | Two selected legal living opponents; audited draft only if lawful |

This completes Transparency coverage for all ten approved web hero
specializations. It does not create a generic preview fallback.

## Background

BATTLE-TRANSPARENCY-001 through -004 established a finite, engine-owned,
revision-bound, typed and read-only preview path. React requests/renders facts;
it must not execute skills, calculate combat, infer state, or predict RNG.

Priest Discipline combines side-dependent hybrid Penance, Redemption-linked
secondary healing, and multi-target Punishment. Audit the live paths before
choosing player-facing wording; legacy code appearance does not prove an effect
is hit-gated, serializable, or safe to promise.

### Owner design decision — 2026-10-08

Holy Word Redemption linked healing from opponent-targeted Penance is intended
to activate **only when Penance causes valid direct damage to its target**. A
target protected by Shield of Protection must continue to show `Damage 0 ·
Blocked` and must receive no linked Redemption healing. Evasion likewise
produces no linked healing. The existing live callback behaviour that heals
Redemption holders after a blocked Penance is a combat-mechanics bug, not a
preview-only display issue.

The owner approved the revised source-backed engine-and-preview proposal on
2026-10-08. The implemented rule defines valid direct damage as a positive HP
loss by the selected target after its authoritative live damage receipt—not raw
attempted damage. It covers Shield/immunity/zero-damage and evasion boundaries,
preserves event ordering and deterministic safety, and remains a minimal
Penance-local engine plus finite-preview change.

## Requirements

- Record a dated source-cited audit of the three live callbacks, hybrid target
  dispatch, formation/receipt/evasion, Redemption ownership/duration,
  Punishment application/tick lifecycle, secondary healing order/coefficient,
  status manager, adapter serialization, legality, cooldowns, and AI/forced
  compatibility. Escalate real legacy ambiguity rather than changing mechanics.
- Penance ally selection shows authoritative Healing and Target HP, no Hit
  Chance. Opponent selection shows Damage, direct-evasion Hit Chance, Target
  HP, and only audited recipient-specific immediate Redemption-linked healing.
- For opponent Penance, a linked Redemption-healing row may appear only when
  the audited result establishes valid direct target damage. It must be absent
  for Shield of Protection, other audited zero-damage/immunity outcomes, and
  evasion; do not show a healing row merely because raw attempted damage exists.
- Holy Word Redemption shows only the current audited application/refresh and
  immediate player-facing meaning; never promise an exact later heal or a
  generic cooldown rule.
- Holy Word Punishment shows per-target direct facts and its audited current
  debuff boundary. It may use lawful draft/full pair previews, but never shows
  aggregate damage, future DoT totals, or relaxed real command cardinality.
- Keep facts finite, typed, recipient-specific, and server-authored. Preview
  unavailable is preferable to invented precision and never blocks a legal
  command.
- Preserve all prior Transparency compatibility, target selection, commands,
  event/audio ordering, formation, responsive behaviour, and accessibility.

## Engine and Contract Requirements

- Use small named pure primitives only where they mirror audited immediate live
  behaviour. Never call `Skill.execute`, callbacks, `resolve_targets`, adapter
  `_resolve`, status updates, or random helpers in preview.
- Under the current session lock, validate revision, current actor, audited
  available skill, target side/ID/liveness, count, duplicates, and Penance's
  side-dependent lawful target shape.
- Do not mutate HP, stats, statuses, buffs/debuffs, durations, cooldowns,
  events/logs/cursors, command results, turns, revision, session RNG, or
  process RNG. Same-seed commands after preview must equal untouched controls.
- Extend the typed consequence/secondary-recipient contract only when needed;
  do not serialize arbitrary status maps or add generic fallbacks.

## Frontend Requirements

- Add exactly the three confirmed Discipline skill IDs to the finite preview
  allowlist; no generic Priest fallback.
- Render server-provided side-aware Penance, Redemption, and Punishment facts
  only. TypeScript must not choose Penance's branch, calculate ranges/chances/
  healing, infer linked allies, or alter target shapes.
- Reuse established hover/focus/pinned compact cards, draft/full multi-target
  selection, stale/abort guards, accessibility, pointer/keyboard/touch,
  responsive layout, and AUDIO-002 behaviour.

## Out of Scope

- Other heroes, generic all-roster preview, battle-balance/mechanic changes,
  Priest Discipline unlock/progression work, full status encyclopedia, future
  periodic-damage totals, generic proc simulation, raw formulas, UI redesign,
  and sound/VFX changes.

## Relevant Files

- `heroes/priest.py`, `heroes/hero.py`, `skills/skill.py`, and status services.
- `battle_api/adapter.py`, `battle_api/models.py`, `battle_api/app.py`.
- `web-ui/lib/battle/types.ts`, `liveProvider.ts`, `useBattlePreview.ts`,
  `web-ui/components/battle/BattleScreen.tsx`, and `web-ui/app/globals.css`.
- Existing/new Transparency tests plus GDD, Technical, web UI contract/style,
  analysis, and tracking documentation named in the detailed brief.

## Acceptance Criteria

1. All three Discipline active skills have truthful pre-confirmation preview,
   completing all ten approved web specializations.
2. Penance correctly differentiates lawful ally-healing and opponent-damage
   branches with no client combat logic.
3. Redemption/Punishment show only audited immediate application, refresh,
   linked-recipient, and status facts; no future DoT or invented result.
4. Punishment retains lawful draft/full selection without aggregate totals or
   altered command shape.
5. Preview purity/RNG safety and existing UI/engine/audio/formation/
   accessibility compatibility are proven.
6. Audit, tests, validation, contracts, documentation, and completion evidence
   accurately record complete-roster scope and known deferrals.

## Validation Required

- Add backend/API tests covering both Penance sides, range/receipt/evasion/
  formation, legality, Redemption ownership/refresh, Punishment draft/full,
  status/secondary recipient facts, stale/dead/wrong-side/duplicate rejection,
  and all prior-scope compatibility.
- Deep-compare state/RNG before and after accepted/rejected previews, patch
  random helpers to fail, and prove same-seed command equivalence.
- Add frontend tests for side-aware facts, typed result rows, multi-target
  selection, stale/error/compact states, all input/accessibility paths, no
  formula duplication, and unchanged command/audio flow.
- Run focused/broader backend/frontend regressions, typecheck, lint, production
  build, Python compile, diff check, and honest 1v1/2v2/3v3 manual checks.

## Agent Assignments

**Complexity/risk:** High. Hybrid side-dependent targeting, multi-target
preview, status lifecycle, linked recipients, engine/API contract, frontend,
deterministic safety, and full-roster completion require all five configured
roles. Dispatch and record all five before implementation.

- **project-manager:** audit/build/review sequencing, scope, roles, documents,
  and completion evidence.
- **game-engine-developer:** live-rule audit, pure primitives, adapter/API,
  status/secondary-recipient truth, and no-mutation/RNG guarantees.
- **ui-developer:** typed side-aware presentation, interaction, accessibility,
  responsiveness, and frontend documentation.
- **test-automator:** deterministic hybrid/multi/status/purity/compatibility
  matrix and integrated regression coverage.
- **reviewer:** independent mechanics, contract, UI, validation, and docs review.

## Completion Notes

Completed the finite Priest Discipline transparency scope and the approved
Penance mechanics correction. Opponent Penance now invokes same-caster Holy
Word Redemption linked healing only after the selected target loses HP from
the authoritative damage receipt. Shield of Protection and fully absorbed
Holy Word Shell now produce no linked healing; partial and ordinary positive
receipts preserve it. Preview remains read-only and reports only finite,
server-authored facts; mixed zero/positive linked receipt ranges are
unavailable rather than guessed.

All five required roles contributed in the staged workflow: project manager
for scope/gates, engine for source audit and adapter/engine work, UI for typed
presentation, test automation for deterministic parity coverage, and the
independent reviewer for final approval. See the corresponding 2026-10-08
BATTLE-TRANSPARENCY-005 entry in `docs/Codex/Completed.md` for complete
validation and manual-browser evidence.
