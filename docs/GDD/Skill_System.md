# Skill System

## Scope and Authority

Skills are specialization-defined engine actions. Python determines availability,
targets, resolution, cooldowns, status effects, and outcomes. UI names,
descriptions, glyphs, and art are presentation metadata unless separately
curated as authoritative design.

## Skill Model

The active `Skill` model carries an initiator, name, concrete callback, target
type (`single` or `multi`), skill type, target quantity, instant/casting and
interrupt/control flags, availability, cooldown state/counter, damage nature/
type, optional independent-effect callback, and last per-target outcome.

Implemented broad types include `damage`, `healing`, `damage_healing`, `summon`,
and `buffs`. There is no general passive-skill framework; reactive behavior is
embedded in hero or status code.

## Activation and Targeting

An ordinary command requires an active directive that accepts player input and
an available, off-cooldown skill. The adapter publishes legal actor, skill,
target count, and living target IDs. Damage targets opponents; healing/buffs
normally target allies; hybrid actions can use both sides; summons and self
skills can need no selected target. Named skills may legitimately override
generic targeting behavior.

## Execution Pipeline

`Skill.execute` applies generic target gates and dispatches to the concrete
hero callback. Damage actions use per-target death/evasion/immunity/hit logic;
healing, hybrid, summon, and buff actions have separate paths. The engine
records the latest outcome for each target, so consumers must not infer an
evade from damage text or a zero amount.

Harmful target-side effects belong to the hit-gated callback and do not apply
to an evaded target. A mixed-effect skill may explicitly register an
independent caster/ally callback; that benefit can resolve even when its harmful
target evades. Current registrations are Crusader Strike, Shield of Righteous,
Heroric Charge (current implementation spelling), Cumbrous Axe, and Shield
Lash. New mixed effects must use this boundary rather than a skill-name special
case in shared resolution.

### Attack Type and Formation Compatibility

`Skill.attack_type` is the authoritative optional classification for approved
damage skills. `Skill.execute` uses a backwards-compatible bound-method
dispatcher: it supplies the value only to a concrete skill method that declares
an `attack_type` parameter, leaving legacy signatures unchanged. A migrated
skill passes the same value and its attacking hero to `Hero.take_damage`; the
engine's single damage-calculation path then applies an authorized
formation-position modifier once.

This is deliberately limited to the currently classified Warrior Weapon Master,
Warrior Defence, Warrior Berserker, Mage Comprehensiveness, Paladin
Retribution, Paladin Protection, Paladin Holy, Priest Comprehensiveness, and
Priest Discipline skills. The owner-approved Paladin/Priest inventory is:

- Hammer of Anger and Holy Blast — `ranged_projectile`;
- Crusader Strike and Shield of Righteous — `melee`;
- Hammer of Revenge, Heroric Charge, Holy Smite, Shadow Word Pain, Penance,
  and Holy Word Punishment — `ranged_instant`.

For hybrid Penance, only its opponent/direct-damage branch receives the
classification; its ally/healing branch remains healing-only. Periodic damage
from classified status skills remains unclassified. `melee`,
`ranged_projectile`, and `ranged_instant` are not generic UI labels or default
values for other skills. The classification stays on `Skill`, not in individual
damage formulas or the frontend.

## Damage, Healing, Status, and Summon Effects

There is no universal formula or duration model. Concrete callbacks calculate
their own physical/magical/hybrid effects; `Hero` applies HP/healing behavior;
the round-start status manager handles most ticks, expiries, and restoration.
Status stacks and durations are skill/status-specific. Summon skills create
hero-derived combatants without selected targets.

## Cooldowns, Costs, and Casting

Skills use an availability flag plus integer cooldown counter. Counters reduce
at round start, but skill-specific setup and the later availability check mean
raw numbers must not be advertised as one universal turn duration. There is no
implemented mana, stamina, or generic resource cost; API `resourceCost` is
currently null.

Non-instant skills enter casting state and execute later as engine-owned
automatic actions. Interruption behavior remains individual skill/hero logic.
Forced or incapacitated actors may have no ordinary legal action.

## Adapter Representation

For approved web heroes, the adapter derives stable skill IDs, target mode,
maximum targets, current cooldown/availability, and null resource cost. It
accepts `useSkill` commands only. A documented `endTurn` concept is not an
implemented API command and must not be presented as active gameplay.

## Requirements for New Skills

1. Define the specialization callback and explicit target/effect metadata.
2. Keep harmful target effects inside the hit-gated action.
3. Register any independent self/ally benefit explicitly.
4. Set and test cooldown/casting/status behavior in its real lifecycle.
5. Add adapter/UI presentation metadata without duplicating rules.
6. Add deterministic behavior coverage before treating the skill as canonical.

## Known Limitations and Open Questions

- No approved resource economy or passive framework.
- No single cooldown, duration, damage, or immunity taxonomy is authoritative.
- Legacy spellings, notably `Heroric Charge`, require owner approval before
  player-facing renaming.
- Full skill descriptions/icons and complete stable IDs outside the approved
  roster are not engine-owned design data.

## Change Log

- 2026-08-06 — Rebuilt from current Skill, Hero, status-manager, and adapter
  behavior; retained hit-gated and independent-benefit combat invariants.
