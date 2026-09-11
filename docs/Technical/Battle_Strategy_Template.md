# Battle Strategy Template

## Purpose

This is the required template for new structured computer strategies. It keeps
combat authority in the engine and makes strategy decisions explainable,
legal, and testable without changing skill mechanics.

## Study-first gate

Before modifying a specialization strategy, create a dated record in
`docs/Codex/Analysis/` that evidences:

1. runtime facts and skill availability/cooldowns;
2. actual skill metadata and effects, including status stack/refresh/cap rules;
3. formation and adapter target legality/cardinality rules;
4. intended existing interlocks and unknown owner decisions; and
5. ordered priorities plus deterministic unit/integration test cases.

Do not infer mechanics from a skill name, frontend treatment, or class
stereotype. Preserve a code/design conflict and request owner direction.

## Required Part A / Part B / Part C layout

### Part A — bounded authoritative information

Create a small per-combatant snapshot and current-turn collector. Include only
facts needed for the hero's decisions: alive state, HP ratio, position,
relevant current/original stats and resistances, status flags, required
Buff/Debuff records with initiator/duration, stacks/durations, and skill
availability/cooldown state. Build stable living ally/opponent pools and
candidate target subsets.

### Part B — ordered explainable analysis

Use a short first-match-wins priority order. Each rule must cite a live fact or
implemented interlock. Prefer deterministic stable ties (for example HP ratio,
relevant resistance, then a stable identity). If a deliberately random tactical
choice is approved, use only the existing seeded battle RNG and document why.

Do not duplicate damage/healing calculations or change status, cooldown,
target, formation, or balance rules. Reject dead, unavailable, cooling,
wrong-side, screened-melee, duplicate, or wrong-cardinality candidates before
returning an action.

### Part C — live hook handoff

`ai_choose_skill` stores the exact chosen skill and target/target list.
`ai_choose_target` returns the compatible saved selection. Do not execute the
skill in strategy code, bypass `Skill.execute`, or rely on adapter random
fallback/target completion as normal behavior. Targetless skills return no
target. Flexible skills select one valid side per action unless their defined
metadata explicitly permits otherwise.

## Required evidence

For every strategy, add deterministic tests for core priorities and at least
one guardrail. Exercise the live computer adapter path in seeded 1v1, 2v2, and
3v3 scenarios. Assert the selected skill is currently legal and that exact
alive, unique, correctly sized targets reach the emitted action unchanged.
Cover unavailable/cooldown state, dead targets, formation screening where
relevant, status stack/refresh boundaries, healing triage, flexible side choice,
and required multi-target cardinality. Make adapter fallback fail in at least
one valid-selection integration test so tests prove the strategy, not repair
logic, supplied the result.
