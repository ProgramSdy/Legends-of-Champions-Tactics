# Combat System

## Purpose

Authoritative design for combat rules and battle flow.

## Battle Flow

_To be documented from the agreed design and current implementation._

## Turn and Action Rules

_To be documented._

## Targeting

_To be documented._

## Damage, Healing, and Status Effects

Attack resolution is authoritative per target. A target that evades an attack:

- takes no damage from that attack;
- does not receive harmful statuses, control effects, damage-over-time effects,
  or other target-side effects from that attack; and
- is reported to clients as having evaded.

A landed attack may legitimately deal zero damage after the engine's damage
calculation. Zero damage does not by itself mean that the attack was evaded, so
valid on-hit effects may still resolve.

For multi-target attacks, the engine resolves hit, evasion, immunity, and death
independently for each target. Target-side effects receive only the targets on
which the attack resolved as a hit.

An attack can also declare a beneficial caster or ally effect that is
independent of hitting its harmful target. Such an independent benefit may
resolve even when the target evades. Shield of Righteous retaining its caster
defense benefit is the reference behavior.

## Victory and Defeat Conditions

_To be documented._

## Open Design Questions

- None recorded yet.

## Change Log

- 2026-07-26 — Initial document created.
- 2026-07-31 — Documented authoritative per-target attack outcomes, zero-damage
  hits, evade suppression of harmful target effects, and independent beneficial
  effects.
