# Hero System

## Scope and Authority

This document describes current battle heroes. It does not define a persistent
collection, levelling, equipment, or rarity system because none is implemented.

## Hero Identity

An engine hero has a runtime name, faculty, specialization (engine field
`major`), derived profession lookup key, group/side, control ownership, skills,
and battle state. Runtime names and Python objects are not stable API identity.
The web adapter therefore adds stable definition IDs and combatant IDs.

Use the terms consistently:

- **Faculty** — broad archetype, such as Warrior or Mage.
- **Specialization** — public/API name for `major`.
- **Profession** — internal concatenation of faculty and specialization.
- **Combatant** — one battle-local hero or summon instance.

## Approved Web Roster

| Definition ID | Faculty | Specialization |
|---|---|---|
| `hero.priest.comprehensiveness` | Priest | Comprehensiveness |
| `hero.priest.discipline` | Priest | Discipline |
| `hero.paladin.retribution` | Paladin | Retribution |
| `hero.paladin.protection` | Paladin | Protection |
| `hero.paladin.holy` | Paladin | Holy |
| `hero.mage.comprehensiveness` | Mage | Comprehensiveness |
| `hero.warrior.defence` | Warrior | Defence |
| `hero.warrior.weapon_master` | Warrior | Weapon Master |
| `hero.warrior.berserker` | Warrior | Berserker |
| `hero.rogue.comprehensiveness` | Rogue | Comprehensiveness |

The legacy engine contains additional specializations across Warrior, Mage,
Paladin, Priest, Rogue, Necromancer, Warlock, and Death Knight. Generator and
simulation lists differ again. Those catalogues are legacy implementation
coverage, not an approved web roster or progression tree.

## Core Attributes

Heroes have current/maximum HP, damage, defence, agility, magic-resistance
compensation, evasion capability, and fire/frost/arcane/shadow/death/poison/
nature resistances. They also retain original-stat snapshots for temporary
effects. Skills, statuses, casting, healing modifiers, resistance modifiers,
allies/opponents, and cooldown state are battle-local state.

## Attribute Generation and Balance Data

Base ranges are loaded from the project's Excel property/resistance data. Hero
generation is randomized and intentionally correlates trade-offs such as HP
versus damage and defence versus agility/resistance compensation. A displayed
hero's starting values are therefore not fixed solely by specialization. Balance
governance and accepted ranges remain owner decisions.

## Control and Team Composition

The web path supports 1v1, 2v2, and 3v3. Friendly heroes are player controlled;
the enemy side can be player or computer controlled. The engine may override
ordinary control for forced, automatic, casting, or restricted states.

No formal tank/healer/damage/support metadata is encoded as authoritative hero
data. Such labels may be useful design interpretation, but must not be treated
as engine rules. Repeated selections and cross-team overlap are allowed for
player/specified-enemy teams; random enemy construction samples without
replacement.

Every hero has an engine-owned battle `position` of `front` or `rear`.
Construction defaults to `front` for legacy simulations, generators, summons,
and 1v1 battles. In an adapter-created 2v2 or 3v3 battle, the ordered team and
its size-specific formation assign the position through the hero constructor.
The 2v2 mappings are `front-rear` (front/rear) and `side-by-side`
(front/front). The 3v3 mappings are `one-front-two-rear` (front/rear/rear),
`two-front-one-rear` (front/front/rear), and `all-front`
(front/front/front). The position is stable battle state and is serialized for
clients; React does not derive or author it from a visual slot.

Combat position is not the same as visual depth. In a 3v3 scene the
owner-approved nearest/middle/furthest order is formation-, side-, and ordered
slot-specific. That visual ordering changes image scale and stacking only; it
does not change the engine-owned front/rear value, target legality, damage, or
hero identity.

## Summoned Units

Water Elemental, Skeleton Warrior, Skeleton Mage, Void Rambler, and Flesh
Puppet are current factory summon types. A summon is a hero-derived combatant
with a master, duration, race, AI, and skills. Master defeat defeats its live
summon; summon defeat clears the master's active-summon reference. The engine
does not establish one universal single-summon cap or guaranteed activation
timing.

## Progression and Upgrades

The default local profile persists ownership of the ten approved web
definitions. Five definitions start locked to player selection: Paladin
Protection, Retribution, and Holy; Warrior Berserker; and Warrior Defence.
They remain valid static definitions and can appear as fixed structured-stage
enemies. The backend unlocks each only through its specified training reward
and returns the authoritative available definition IDs to the client. Battle
local buffs/debuffs are not progression.

Levels, XP, permanent attributes, rarity, equipment, inventory behavior,
multiple profiles, accounts, and cloud sync remain unimplemented.

## Open Questions

- Canonical release roster and expansion policy.
- Fixed versus randomized stat communication to players.
- Formal role labels, duplicate-hero restrictions, and summon limits.
- Excel ownership, balance review process, and persistent progression design.

## Change Log

- 2026-08-15 — Added the three adapter-owned 3v3 position mappings while
  retaining the existing constructor default for legacy paths.
- 2026-08-19 — Documented the default-profile ownership gate used by the two
  persisted training curricula.
- 2026-08-14 — Documented the backward-compatible hero position field and
  authoritative 2v2 constructor mapping.
- 2026-08-06 — Rebuilt from current hero, generator, summon, and adapter
  behavior; separated approved web roster from legacy catalogue scope.
