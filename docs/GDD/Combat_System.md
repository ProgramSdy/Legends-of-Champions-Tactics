# Combat System

## Scope and Authority

Python is authoritative for combat. The web/API layer publishes commands,
snapshots, and events but does not calculate rules. This document describes the
implemented baseline; detailed formulas remain specialization-specific.

## Setup and Teams

The web API accepts two sides of one to three heroes. It supports specified or
random enemy composition and player or computer enemy control. The legacy
engine accepts hero lists more generally. Duplicates and cross-team duplicate
definitions are valid for player and specified-enemy selections; random enemy
composition samples the approved roster without replacement.

Two-versus-two battles additionally use one formation per side. `front-rear`
assigns the first ordered hero to `front` and the second to `rear`;
`side-by-side` assigns both to `front`. The friendly formation is required at
the HTTP boundary. A player-controlled enemy formation is also required, while
a computer-controlled enemy may omit it so the adapter selects one of the two
formations from the session-seeded random stream. One-versus-one and
three-versus-three heroes retain the compatible `front` default and do not
accept formation input.

## Round Lifecycle

At round start, defeated summons are cleaned up, ally/opponent relationships
refresh, cooldown counters decrease, living heroes process status effects, and
victory is checked. Living combatants are then ordered by descending current
agility. Status changes therefore happen before that round's initiative is
captured.

Each queued living hero receives an engine directive: player command,
computer action, forced action, automatic casting/vanish action, or a skip.
Legacy `Game.hero_action` re-sorts the remaining queue after each action;
the supported web/API adapter removes the acting hero but retains the
round-start queue order. Agility-changing effects can therefore affect later
ordering differently between paths. Equal-agility design intent is unconfirmed.

## Action and Target Rules

An action requires an available, off-cooldown skill and a target shape accepted
by the active directive. Legal API actions publish the acting combatant, exact
target count, and living valid targets. Player clients cannot issue ordinary
commands during engine-owned automatic, forced, restricted, or ended states.

Formation targeting is currently authoritative only for damage skills whose
Warrior-owned `Skill.attack_type` is `melee`, `ranged_projectile`, or
`ranged_instant`. A melee action cannot target a living rear defender while
any living front defender exists; after the last front defender is defeated,
the rear target becomes legal. The adapter applies the same legal target set to
player commands, forced actions, and computer target selection. Missing,
`NA`, or future attack types retain the pre-formation target behavior.

## Per-Target Attack Resolution

For damage skills, every target independently follows this conceptual order:

1. ignore defeated targets;
2. resolve evasion;
3. resolve all-damage and physical/magical damage-nature immunity;
4. resolve control immunity where the attack applies control; then
5. resolve a landed hit and its hit-gated harmful effects.

An evade causes no damage or harmful target-side effect from that attack. A
landed attack may still deal zero after its own calculation; zero damage is not
evidence of evasion. Multi-target skills pass only landed targets to harmful
on-hit actions. Approved independent caster/ally benefits may still occur on a
miss; Shield of Righteous is the reference behavior.

Healing and hybrid skills have their own paths and must not be assumed to use
the full damage-immunity pipeline.

## Damage, Healing, and Resistance

There is no single universal damage formula. Concrete skills calculate physical,
magical, or hybrid damage from their own inputs, commonly including damage,
defence or one of seven resistances, and random variation. HP never falls below
zero. Healing applies its current boost/reduction modifiers, cannot be
negative, and is capped at maximum HP.

Core resistance schools are fire, frost, arcane, shadow, death, poison, and
nature. Exact coefficients, floors, and balance intent remain skill/data
specific.

For the approved Warrior attack types, the skill first produces its existing
final damage value. `Hero.take_damage_calculation` then applies exactly one
position adjustment before shields and HP mutation:

- rear-attacker melee deals 70%; front-attacker melee is unchanged;
- ranged projectile front-to-front is unchanged, front-to-rear and
  rear-to-front deal 87.5%, and rear-to-rear deals 75%;
- ranged instant is unchanged.

The adjusted value uses `floor` after multiplication and is then clamped to
zero. These rules currently apply only to Warrior Weapon Master, Warrior
Defence, and Warrior Berserker skills that already declare an approved attack
type; no attack type is inferred for another faculty.

## Status, Control, Casting, and Cooldowns

Statuses are implemented as hero flags, counters, attributes, and optional
records—not one uniform status class. Most tick at round start; duration,
stack, spread, dispel, restoration, and expiry semantics are status-specific.
Control directives include skip states such as stun/paralysis/fear and forced
Scoff behavior. Non-instant casts become automatic later actions and may be
interrupted by specialization-specific behavior.

Cooldowns decrement at round start. Individual skills set their own counters;
do not translate every raw counter into one universal number-of-turns rule.

## Summons

Summons are hero-derived combatants linked to a master, skills, AI, and a
duration. They can participate in side/turn collections, expire through status
processing, and are defeated when their master is defeated. Same-round queue
insertion is not fully consistent across summon paths and is not a guaranteed
design rule.

## Outcomes and Round Limit

Exactly one living group wins; no living group is a draw. The configured cap is
15, but the current increment/check placement normally permits actions in
rounds 1–14 and produces a round-limit result on the next transition. It does
not currently choose a HP/tiebreak winner. Whether this is intended requires
owner confirmation.

## Known Limitations and Open Questions

- Canonical initiative tiebreak, round-cap semantics, and tie resolution.
- Status duration/classification tables are not yet a validated design taxonomy.
- Evasion-cap intent and universal damage-formula intent are unconfirmed.
- Summon capacity and same-round activation are not consistently guaranteed.

## Change Log

- 2026-08-14 — Added authoritative 2v2 formations, Warrior attack-position
  target legality, and one-time floor-and-clamp damage adjustments.
- 2026-08-06 — Rebuilt from current engine and adapter behavior; retained the
  existing per-target evade and independent-benefit invariant.
