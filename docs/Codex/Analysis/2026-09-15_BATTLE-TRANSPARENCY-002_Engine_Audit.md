# BATTLE-TRANSPARENCY-002 Engine-First Audit

**Date:** 2026-09-15  
**Scope:** Priest Comprehensiveness and Paladin Retribution only  
**Phase:** Pre-implementation study; no gameplay, API, or UI behavior changed

## Boundary and evidence

This audit follows the live path from `Skill.execute` into the six approved hero
callbacks and then through `Hero.take_damage` or `Hero.take_healing`. It also
checks the existing BATTLE-TRANSPARENCY-001 preview boundary in
`battle_api/adapter.py`, its Pydantic response models, and its API route.

Authoritative sources inspected:

- `heroes/priest.py`: Holy Smite, Shadow Word Pain, and Binding Heal.
- `heroes/paladin.py`: Hammer of Anger, Crusader Strike, and Flash of Light.
- `skills/skill.py`: target resolution, evasion, immunity, and independent
  effect execution.
- `heroes/hero.py`: formation damage and healing receipt behavior.
- `battle_api/adapter.py`, `battle_api/models.py`, and `battle_api/app.py`:
  legality, revision/session locking, evaluation, response validation, and the
  async HTTP boundary.
- Existing BATTLE-TRANSPARENCY-001 tests and frontend contract consumers.

The preview must continue to inspect live state only. It must never call
`Skill.execute`, a hero skill callback, `take_damage`, or `take_healing`.

## Verified live skill semantics

All ranges below are pre-evasion. Damage receipt and healing receipt are
separate later stages described below.

| Hero / skill | Legal side and range source | Verified immediate result | Material consequence |
| --- | --- | --- | --- |
| Priest — Holy Smite | One living enemy; ranged instant | `19 + randint(-3, 3)`, so 16–22. The callback deliberately ignores defence and every resistance. Ranged-instant formation adjustment is 1.0. | None. |
| Priest — Shadow Word Pain | One living enemy; ranged instant | `round((Priest.damage + randint(0, 5) - target.shadow_resistance) / 2)`, then non-negative damage receipt. Defence and non-shadow resistances do not apply. | If Pain is absent, a successful hit applies it with duration 5. An existing Pain is neither refreshed nor strengthened. The later DoT amount must not be previewed: the live callback can use another random roll when direct damage is non-positive. |
| Priest — Binding Heal | One living ally, including self | Selected target base 22–28. The target's healing receipt modifier and missing-HP cap apply. | When another ally is selected, the Priest receives a separate independent base heal of 17–23, using the Priest's own receipt modifier and missing-HP cap. Omit this consequence when it cannot change the Priest's HP. Self-targeting performs only the selected-target 22–28 heal. |
| Paladin — Hammer of Anger | One living enemy; ranged projectile | First calculate `max(Paladin.damage + randint(-2, 2) - target.defense, 0)`. Active one-stack Wrath then adds 3–5; active two-stack Wrath adds 6–8. The total then receives the ranged-projectile formation multiplier. | When active Wrath contributes, expose its separate bonus range and current stack count. No contribution exists when the Wrath status is absent, or when its stack value is outside the live 1/2 branches. |
| Paladin — Crusader Strike | One legal living enemy; melee, so a living front enemy screens rear enemies | Base damage is 18–22 and ignores target defence/resistance. A rear-position caster receives the existing 0.7 melee multiplier; a front caster does not. | Wrath is guaranteed after an accepted action, not merely on hit. First use applies stack 1 and duration 3; the next valid use raises it to stack 2 and resets duration 3; at stack 2 it refreshes duration 3. The independent-effect path intentionally applies/refreshes Wrath even when damage is evaded or prevented. The recipient is the Paladin, not the selected enemy. |
| Paladin — Flash of Light | One living ally, including self | No Wrath: 19–21. Active stack 1: 24–26. Active stack 2: 30–32. Each range receives the selected ally's healing modifier and missing-HP cap. | The first `randint(0, 2)` is still consumed by live execution even when Wrath replaces that amount with a separate bonus roll. Preview must not consume either roll and must not change live RNG order. |

### Direct hit and deterministic prevention

The four damage skills pass through `Skill.resolve_targets`. Evasion is checked
before immunity. The existing direct Hit Chance remains the inverse of that
evasion rule and is valid for Holy Smite, Shadow Word Pain, Hammer of Anger,
and Crusader Strike. Binding Heal and Flash of Light bypass target resolution
and have no Hit Chance.

Every six-skill damage definition currently leaves `damage_nature` at its
default `"NA"`. Therefore `anti_magic_shield` does **not** prevent these skills
under the live implementation, even when their theme is magical. The general
`shield_of_protection` and `glacier` all-damage immunities do prevent them.
Preview must preserve this current behavior; classifying or rebalancing the
skills is outside this task.

Holy Word Shell absorption and Void Connection's target-side damage split are
deterministic receipt facts already mirrored by the audited adapter helper.
They should remain after the skill-specific and formation calculations.

### Healing receipt

`Hero.take_healing` applies:

1. `total_boost = sum(healing_boost_effects.values())`;
2. `total_reduction = min(sum(healing_reduction_effects.values()), 1)`;
3. `modifier = max(0, 1 + total_boost - total_reduction)`;
4. `round(base_healing * modifier)`;
5. HP capped at `hp_max`.

The truthful immediate preview amount is therefore the actual HP delta:
`min(missing_hp, rounded_modified_healing)`. A full-HP legal target is 0–0.
A 100% reduction is not necessarily full prevention if a healing boost is also
active, because the live formula combines both into the same net modifier.

## Recommended narrow pure primitives

Implementation should extract small calculation helpers in the owning hero
classes and use the same helpers from live callbacks and preview range methods:

- Priest: Holy Smite direct damage, Shadow Word Pain direct damage, Binding
  Heal selected-target base amount, and Binding Heal caster base amount.
- Paladin: Hammer base damage plus explicit Wrath bonus, Crusader Strike base
  damage, and Flash of Light base amount for the current Wrath state.
- Hero: a read-only healing receipt calculation shared by `take_healing` and
  preview; mutation remains only in `take_healing`.

The refactor must preserve the number and order of live RNG calls. In
particular, Flash of Light consumes an initial 0–2 roll even in both Wrath
branches, Crusader Strike consumes its nominal 100% activation roll, and
Shadow Word Pain may consume a separate future-DoT roll. Range helpers accept
candidate boundary values; they do not call `random`.

The existing `audited_direct_damage_range(skill_name, target)` convention can
be extended to these four damage skills. A separate audited healing-range
method should return the selected-target range and, for Binding Heal only, a
separate caster range. Do not overload the damage method with healing.

## Additive typed contract decision

The request model and endpoint path need no change. All six skills are
single-target and fit the existing `targetIds` constraints. The current
session lock, current-actor check, revision check, published legal-action
lookup, side/liveness validation, and target cardinality checks remain the
authority boundary.

The response needs these additive capabilities:

- `primary.kind` accepts `healing` in addition to `damage` and `prevented`.
- `directHitChancePercent` is nullable/omitted for healing and remains required
  and numeric for damage/prevented target facts.
- New typed consequence variants:
  - Shadow Word Pain application: `onHit`, only while currently absent.
  - Binding Heal secondary healing: `always`, with `recipientId` identifying
    the Priest and a capped `amountRange`; emit only when HP can change.
  - Hammer Wrath bonus: `always`, with current `stacks` and an effective
    target-HP-facing extra-damage `amountRange` after current formation and
    deterministic receipt, only for active stack 1 or 2. The live pre-scale
    rolls are 3–5 or 6–8, but presenting those raw values as the player's
    immediate bonus would mislead in rear/rear or mixed-position attacks.
  - Crusader Wrath outcome: `always`, with `recipientId` identifying the
    Paladin, resulting `stacks`, and an outcome discriminant for first
    application, next stack, or duration refresh.

Use a discriminated consequence union in Pydantic and TypeScript so invalid
field combinations are rejected. Existing bleed/poison/cold JSON remains
unchanged. Existing Mage/Rogue target facts continue to carry numeric Hit
Chance. The response remains an additive `contractVersion: "1.0"` change if
those existing payloads and fields are preserved exactly.

Expected OpenAPI delta is confined to the preview response components: the
new `healing` primary enum member, nullable direct Hit Chance, and the new
consequence variants/fields. There is no route, request, command, snapshot,
event, authentication, persistence, or save-data delta.

## Evaluator sequencing

For each validated target:

1. Identify whether the skill is damage or healing from the approved
   actor/skill allowlist.
2. For damage, evaluate deterministic immunity, then the audited raw boundary
   values, formation adjustment, absorption/link receipt, and material
   consequence. Crusader's actor-owned Wrath consequence remains present even
   when deterministic prevention makes primary damage 0.
3. For healing, evaluate audited base boundary values, the recipient's current
   healing modifier, Python rounding, and missing-HP cap. Do not run damage
   prevention or calculate Hit Chance.
4. Evaluate Binding Heal's caster receipt independently when the target is not
   the caster.
5. Return the request's current revision, actor, skill, and exact target IDs so
   the existing client stale/abort checks remain authoritative.

## No-mutation, RNG, async, and transaction invariants

- Preview retains `session.lock` and never installs `session.rng_state` into
  global `random`.
- Patch `random`, `randint`, `choice`, `sample`, and `shuffle` to fail during
  all six preview paths.
- Deep-compare HP/max HP, attributes, statuses, stacks, durations, cooldowns,
  buffs/debuffs, healing modifier dictionaries, formations, turn queues,
  revision, event sequence/logs, command cache, adapter snapshot, session RNG,
  and global RNG before/after success and rejection.
- Compare a later seeded live command with an untouched same-seed session.
- The FastAPI operation remains genuinely `async` and sends the lock-bound,
  synchronous engine inspection through `asyncio.to_thread`, avoiding event
  loop blocking. Pydantic validation occurs before engine access.
- Preview has no database or persistence path and opens no transaction. Its
  rollback equivalent is strict state identity after success, validation
  failure, or evaluator failure.

## Required backend validation matrix

- Exact endpoint ranges at relevant formation pairs, defence/resistance
  boundaries, HP caps, full HP, boost/reduction combinations, and absorption.
- Wrath absent, active stack 1, active stack 2, and refresh; include evaded and
  prevented Crusader Strike to prove its independent effect semantics.
- Shadow Word Pain absent versus active, including non-positive direct damage;
  never expose a future DoT total.
- Binding Heal self versus another ally, separately modified recipients, full
  caster, full target, and zero-effective-healing states.
- Wrong target side, dead target, screened rear melee target, stale revision,
  wrong actor, cooldown/unavailable skill, duplicate/invalid ID, and all
  out-of-scope heroes/skills.
- Existing Mage/Rogue payload equality, Arcane draft/cardinality behavior, API
  404/409/422 shapes, and later-command seeded equivalence.

## Known legacy ambiguities and out-of-scope findings

1. Hammer of Anger's combat log calls its Wrath bonus "Shield of Righteous";
   the condition and stack data are unambiguously Wrath of Crusader. Preview
   should use the truthful Wrath name. Correcting the legacy battle log is not
   part of this task.
2. The skill definitions do not classify their damage nature, so anti-magic
   immunity does not apply. Do not infer a magical nature in preview.
3. Shadow Word Pain records duration 5 beside a comment saying four rounds.
   Preview only reports a new application and must not promise duration or
   future total.
4. Crusader Strike's independent effect on evade/immunity is established and
   tested behavior. Treating Wrath as `onHit` would be false.
5. Healing has no named prevention reason in the live receipt boundary. A
   reduced/capped 0–0 result should remain a `healing` primary unless the owner
   later introduces an authoritative healing-prevention rule and reason ID.

These findings do not block the scoped implementation. They constrain it.
