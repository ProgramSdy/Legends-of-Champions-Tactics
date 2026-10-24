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
and `buffs`. `Skill.is_passive` explicitly distinguishes engine-triggered
passives from selectable commands. Holy Aura and Blood Frenzy are registered
passives in the approved web roster; their activation and lifecycle remain
engine-owned rather than player commands.

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

The current approved hero roster assigns an initial cooldown counter of two
to Rogue Comprehensiveness's Shadow Evasion, and three to Warrior Defence's
Shield Bash/Thunder Pot, Warrior Weapon Master's Antivenom Potion, Warrior
Berserker's Warlust, Paladin Protection's Heroric Charge, and Paladin Holy's
Shield of Protection. The Gallery shows these assigned counts as `N Rounds`;
all other current skills omit the Cool Down fact. This is catalogue reference
metadata, not a change to cooldown ticking or a promise of an exact future
availability turn.

Non-instant skills enter casting state and execute later as engine-owned
automatic actions. Interruption behavior remains individual skill/hero logic.
Forced or incapacitated actors may have no ordinary legal action.

## Adapter Representation

For approved web heroes, the adapter derives stable skill IDs, target mode,
maximum targets, current cooldown/availability, and null resource cost. It
accepts `useSkill` commands only. A documented `endTurn` concept is not an
implemented API command and must not be presented as active gameplay.

### Hero Gallery reference metadata

The static Hero Gallery catalogue separately presents each approved skill's
adapter-audited player-facing target semantic, skill type, classifications, and
base Damage/Healing reference state. This metadata is not a command, live
legality result, or battle preview. A numeric reference is published only after
an exact formula-bound audit; it describes baseline skill power before target
receipt rules and does not predict a combat result. Target-dependent or
otherwise unproved values are explicitly unavailable. `Unclassified` means a
damage concept applies but the engine definition omits that classification;
`Not applicable` means the concept does not apply. The frontend consumes the
typed result and does not derive it from `target_type`, source code, or formulas.

#### Standard for future Gallery skills

Apply this reference design to each newly added or changed hero/skill, including
passives. Inspect the live skill and its complete resolution and status paths;
do not infer mechanics from the introduction or a raw target type. Register
stable hero/skill IDs and the correct Active Skills or Passive classification.
Publish only applicable, audited target, skill-type, attack-type, damage-nature,
and damage-type facts. A missing applicable classification is **Unclassified**;
a genuinely inapplicable field is omitted rather than guessed.

- **Damage and healing:** Show separately labelled **Base Damage** and/or
  **Base Healing** only when relevant. An audited fixed range is baseline skill
  power, not final damage dealt or HP restored. Preserve separate values for
  hybrid branches, ordered targets, and material conditions; do not combine
  immediate and periodic effects or invent a total. Prove boundaries and
  rounding, and use **Unavailable** with an honest reason when not audited.
- **Target-dependent damage:** When the audited formula cannot honestly be
  expressed as a target-independent base range, use **Target-dependent** and
  the shared yellow `?` popup with an engine/adapter-authored formula. Include
  meaningful variation, floors, rounding, target inputs, and material
  conditions. This explanatory formula is not a live prediction or a guarantee
  of final HP change. Do not classify an unaudited value as target-dependent
  merely to avoid an unavailable state.
- **Cool Down:** Audit the skill's actual engine-assigned initial counter and
  its activation paths. Publish a positive `cooldownRounds` only when one is
  assigned, and display the **Cool Down** box last as `N Rounds`; otherwise
  omit the box. This is not a status duration, live remaining counter, or an
  exact promise of which future turn the skill is usable.
- **Descriptions and verification:** Maintain editable introductions and
  optional tips in validated Gallery YAML, separate from authoritative typed
  mechanical facts. Descriptive prose may mention audited numeric effects, but
  must agree with the engine and must not become a structured source of game
  rules. Preserve the owner's line breaks and wording. Test catalogue coverage,
  formula/cooldown accuracy, passive non-actionability, content IDs, accessible
  responsive rendering, and unchanged live combat; retain unavailable states
  for facts that cannot yet be proved.

The current audited Target-dependent Weapon Master entries publish their
adapter-authored direct-damage formulas rather than a misleading static
range: Fatal Strike is `max(Caster Damage + Skill Variation − Target Defence,
1)`; Armor Crush is `max(ceil((Caster Damage + Skill Variation − Target
Defence) × multiplier), 1)`, where Armor Breaker uses 55% when absent or at
zero stacks, 65% at one stack, and 75% at two or more stacks. These describe
only direct damage before receipt, not final received damage or guaranteed status
outcomes. Antivenom Potion separately exposes audited self-healing power
18–20 before healing modifiers and the HP cap; it remains a non-damaging buff.

Warrior Defence's Devastate, Shield Bash, and Thunder Pot, and Warrior
Berserker's Moon Slash and Strike of Meteorite also have audited
target-Defence-dependent direct formulas. Their Gallery Base Damage cards show
**Target-dependent** without a note; the existing calculation popup supplies
the corresponding engine-owned formula. Warlust remains non-damaging.

Paladin Retribution's Hammer of Anger, and Paladin Protection's Hammer of
Revenge and Heroric Charge, are also Target-dependent in the Gallery: their
direct damage depends on target Defence. The first two retain their
engine-defined bonus bands from Wrath of Crusader and eligible caster debuffs,
respectively. Crusader Strike and Shield of Righteous instead deal fixed
direct power 18–22. Holy Blast deals 20–25 to the first selected target and
14–17 to the second. Priest Discipline's Penance has separate enemy direct
damage power 17–21 and ally healing power 21–25; Holy Word Punishment has
immediate direct power 7–11. Holy Word Punishment separately publishes
continuous power per later round-start activation: 9–16 for both a newly
created and a recycled debuff. Both paths now use `ceil(1.3 × direct roll)`
for the stored effect, followed by per-activation ±1 variation. A duration of four
therefore produces three later activations; casting into an already-active
Punishment deals its immediate damage without attaching or refreshing the
debuff. These values are pre-receipt power, not promises of final HP change,
status application, or lifetime total damage.

Warrior Berserker's **Blood Frenzy** is an engine-triggered passive, not a
player/AI command. After surviving a damage resolution, it cannot activate
above 50% HP or while already active. At over 25% through 50% HP it has a
50% activation chance; over 10% through 25% HP, 75%; and at 10% HP or less,
activation is guaranteed. On activation it lasts two rounds, grants 20
Agility, and removes `round(current Defence / 2)` Defence, restoring those
stat changes when it expires. While active, Moon Slash and Strike of
Meteorite each restore whole HP equal to `int(calculated direct damage × 0.3)`;
Moon Slash applies this independently per selected target. This is calculated
skill damage, not a promise about target HP lost after receipt modifiers.

## Requirements for New Skills

1. Define the specialization callback and explicit target/effect metadata.
2. Keep harmful target effects inside the hit-gated action.
3. Register any independent self/ally benefit explicitly.
4. Set and test cooldown/casting/status behavior in its real lifecycle.
5. Add adapter/UI presentation metadata without duplicating rules.
6. Add deterministic behavior coverage before treating the skill as canonical.

## Known Limitations and Open Questions

- No approved resource economy or generic passive lifecycle beyond the current
  explicit `is_passive` marker and Holy Aura's status-owned behavior.
- No single cooldown, duration, damage, or immunity taxonomy is authoritative.
- Legacy spellings, notably `Heroric Charge`, require owner approval before
  player-facing renaming.
- Full skill descriptions/icons and complete stable IDs outside the approved
  roster are not engine-owned design data.

## Change Log

- 2026-08-06 — Rebuilt from current Skill, Hero, status-manager, and adapter
  behavior; retained hit-gated and independent-benefit combat invariants.
