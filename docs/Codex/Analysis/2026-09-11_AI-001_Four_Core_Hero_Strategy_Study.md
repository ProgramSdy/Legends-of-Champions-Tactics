# AI-001 Pre-Implementation Study — Four Core Hero Strategies

**Date:** 2026-09-11  
**Gate:** Complete before AI-001 strategy implementation  
**Scope:** Rogue Comprehensiveness, Mage Comprehensiveness, Priest
Comprehensiveness, and Priest Discipline only.

## Authority and execution path

`Hero.ai_action` is the legacy direct executor, but a live computer battle uses
the adapter path: published legal actions are built first, then the hero's
`ai_choose_skill` and `ai_choose_target` run, then the adapter resolves the
chosen action. The adapter sanitizes targets and can use seeded random fallback
to repair an unavailable skill or missing target. AI-001 must not depend on
that repair: a selected strategy must itself return a currently available skill
and a complete compatible target selection.

`BattleAdapter._legal_actions` excludes passive, unavailable, and cooldown
skills. `_valid_target_ids` admits living allies for healing/buffs, living
opponents plus allies for `damage_healing`, and living opponents for damage.
Melee damage is front-screened while a living front defender exists; ranged
skills are not. The adapter currently exposes a reduced `min(target_qty,
valid_targets)` cardinality for a multi-target skill when targets are scarce.
This is not sufficient for AI-001: Arcane Missiles and Holy Word Punishment
must be selected only when two distinct living legal opponents exist.

The `Warrior_Weapon_Master` pattern is the implementation standard:

1. **Part A:** bounded combatant and current-turn facts;
2. **Part B:** ordered explainable tactical selection; and
3. **Part C:** save the selected target(s) with the selected skill and hand
   them back through existing `ai_choose_skill` / `ai_choose_target` hooks.

No strategy may reproduce damage/healing formulas, change `Skill.execute`,
change formation rules, or move authority into the frontend.

## Shared Part A fact boundary

All decisions must read live instance state, not spreadsheet averages:

- `hp`, `hp_max`, derived HP ratio, alive state, `position`, current/original
  defence, agility, and the specialization-relevant resistances;
- active status flags, field-owned stacks/durations, and named Buff/Debuff
  records with their initiator and duration;
- each skill's `is_available`, `if_cooldown`, cooldown value, target type,
  target quantity, and attack type; and
- living ally/opponent pools in stable deterministic order.

The four hero constructors obtain randomized per-instance properties from
`data/Hero_basic_property.xlsx` and `data/Hero_resistance.xlsx`; they are not
fixed class constants. Cooldowns are authoritative only through
`is_available and not if_cooldown`; the raw counter is decremented/cleared by
round-start processing.

Use deterministic ties: stable ordered facts such as HP ratio, relevant
resistance, position, and a stable identity/name. Any intentional use of the
existing seeded battle RNG must be narrowly documented. No broad random
weighted fallback is permitted in the new strategies.

## Verified skill and interlock matrix

### Rogue Comprehensiveness

| Skill | Live metadata | Verified mechanics relevant to strategy |
|---|---|---|
| Sharp Blade | single damage, melee | Direct physical damage after defence. It has a 50% chance to add Bleeding only when absent; duration is 3 and an active bleed is neither refreshed nor strengthened by a repeat cast. |
| Poisoned Dagger | single damage, ranged instant | Direct half-style physical hit; 85% poison application. First use creates a 4-round poison, a second raises stacks to 2, and later casts neither add nor refresh it. Poison tick value depends on the applier damage and target poison resistance. |
| Shadow Evasion | targetless buff, quantity 0 | Sets 100 evasion for duration 1 and a 2-round cooldown. It has value only when hostile turns remain after the Rogue's current turn. |

Sharp is adapter-screened as melee and Poisoned Dagger is ranged. Both legacy
skill action methods omit attack-type propagation to `take_damage`; AI-001 must
preserve that existing mechanics quirk. Relevant target facts are bleed state,
poison state/stacks, defence, poison resistance, HP pressure, hard immunity,
and enemy `actioned` state.

### Mage Comprehensiveness

| Skill | Live metadata | Verified mechanics relevant to strategy |
|---|---|---|
| Fireball | single damage, ranged projectile, magical fire | Uses fire resistance. |
| Arcane Missiles | multi damage, quantity 2, ranged projectile, magical arcane | One shared damage roll, then arcane-resistance damage for every selected opponent. It needs two distinct living legal opponents for AI-001. |
| Frost Bolt | single damage, ranged projectile, magical frost | Uses frost resistance. If Cold is absent, reduces current agility by 70% of original agility and creates duration 2; an active Cold is not refreshed. |

All three are initially available and uncooled. Relevant facts are actual fire,
arcane, and frost resistance, target HP, current/original agility, Cold status
and duration, rank efficiency, living target count, and immunity. All are
ranged, so no artificial melee screening may be added.

### Priest Comprehensiveness

| Skill | Live metadata | Verified mechanics relevant to strategy |
|---|---|---|
| Holy Smite | single damage, ranged instant | Reliable 19±3 damage that ignores defence and resistance. |
| Shadow Word Pain | single damage, ranged instant | Uses shadow resistance. First use sets duration 5 and a DOT; active Pain is not refreshed or strengthened by recast. |
| Binding Heal | single healing | A self target heals self. Another ally heals that ally and independently gives the caster a smaller heal. No cooldown. |

Full-HP healing is legal and deliberately produces a zero-heal presentation,
but it is tactically wasteful when nobody benefits. Strategy facts therefore
include every living ally's missing HP and the caster's secondary-heal value,
target shadow resistance, Pain status/duration, and finish pressure.
Priest Comprehensiveness has no Purification/cure skill in its current kit;
AI-001 must not invent cure logic.

### Priest Discipline

| Skill | Live metadata | Verified mechanics relevant to strategy |
|---|---|---|
| Penance | single `damage_healing`, ranged instant | An ally receives 21–25 healing; an opponent takes 17–21 damage ignoring defence/resistance. Enemy Penance also heals every ally carrying this caster's Redemption. |
| Holy Word Redemption | single ally buff | Adds a same-caster Buff with duration 5/effect 0.7; recast refreshes duration. `Skill.execute` can also apply it to one additional living ally when the caster is ≤75% HP and more than one ally lives. |
| Holy Word Punishment | multi damage, quantity 2, ranged instant | Damages two opponents and creates a same-caster duration-4 Punishment DOT only where absent. Every selected hit can heal same-caster Redemption allies; a repeat active Punishment does not refresh. |

Penance's valid pool is flexible, but a selected Penance action must target one
side only: exactly one living ally for healing or one living opponent for
damage. Redemption/Punishment ownership must inspect the Buff/Debuff name **and
initiator**, not only a shared boolean status. Punishment requires two distinct
living opponents for this task.

## Per-hero priority evidence

Implementation may refine exact ordering only within these recorded facts:

1. **Rogue:** use Evasion for survival only when a later hostile action is
   still possible; use legal kill pressure; establish/raise Poisoned Dagger
   only below its two-stack cap when poison resistance makes it worthwhile;
   establish absent Bleeding; use legal direct damage fallback rather than
   treating capped/active statuses as refreshable.
2. **Mage:** choose a reliable finish/weak-resistance single target; apply
   first Cold to a high-current-agility un-Cold target where control matters;
   choose Arcane Missiles only with a full two-target set; otherwise choose
   resistance-aware Fireball/Frost Bolt with deterministic ties.
3. **Priest Comprehensiveness:** critical meaningful Binding Heal triage first,
   preferring an injured other ally when the caster also benefits; reliable
   Smite finish pressure; establish Pain on a durable unmarked suitable target;
   do not cast a no-value full-health heal or pretend Pain refreshes.
4. **Priest Discipline:** critical ally Penance; finishing enemy Penance;
   establish or refresh this caster's Redemption where it has living ally
   value; choose two-target Punishment only for a genuine legal multi-target
   set, preferring unpunished enemies and existing Redemption synergy; use
   enemy Penance as the legal single-target pressure fallback.

These are tactical priorities, not new mechanics or balance values. The owner
must decide if a future strategy should intentionally recast an active/capped
DOT solely for its direct hit, or intentionally use full-HP healing for
presentation; AI-001 defaults to avoiding the no-added-status/no-value cases.

## Required validation matrix

Reusable test patterns are in `tests/test_warrior_weapon_master_strategy.py`,
`tests/test_warrior_defence_berserker_strategy.py`,
`tests/test_paladin_strategy.py`, and `tests/test_ui018_formations.py`.

- **All four:** assert the chosen skill is available/not cooling; targets are
  alive, legal, unique, exact-cardinality, and consistent with the skill.
  Disable preferred skills to prove a legal fallback. All-unavailable state
  must not fabricate a skill. Use seeded reproducibility.
- **Rogue:** absent/active Bleed, poison stacks 0/1/2, poison resistance,
  Evasion/cooldown/later-enemy-turn conditions, front-screened Sharp versus
  rear-reachable Poisoned Dagger.
- **Mage:** lowest relevant resistance, Cold absent/active, 1v1 never choosing
  Arcane Missiles, and 2v2/3v3 exact two distinct Missile targets.
- **Priest Comprehensiveness:** self-only injury, injured ally plus injured
  caster, full-HP no-value guard, Smite finish, and active Pain boundary.
- **Priest Discipline:** Penance ally and enemy branches, same-caster versus
  other-initiator Redemption, Redemption refresh/extra-target interlock, and
  Punishment only when two valid opponents exist.
- **Integration:** run seeded 1v1, 2v2, and 3v3 computer adapter turns. Assert
  selected skill/target(s) survive into `skillStarted` without adapter random
  fallback/target fill. A monkeypatched fallback that fails on use is required
  where a valid strategy selection exists.

## Study conclusion

The required facts, legal boundaries, status/cooldown behavior, interlocks,
priority rationale, and test matrix are documented. Implementation may begin
only in `heroes/rogue.py`, `heroes/mage.py`, `heroes/priest.py`, focused tests,
and the associated stable technical template/documentation.
