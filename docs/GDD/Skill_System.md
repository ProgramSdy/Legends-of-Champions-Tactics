# Skill System

## Purpose

Authoritative design for active skills, passive abilities, effects, targeting, costs, and cooldowns.

## Skill Types

_To be documented._

## Activation Rules

_To be documented._

## Costs and Cooldowns

_To be documented._

## Effect Resolution

Damage skills resolve their intended targets through the shared `Skill`
boundary before invoking target-side skill behavior. Harmful target effects
must be part of the hit-gated action and must not be applied to an evaded
target.

Mixed-effect attacks must declare any caster or ally benefit that is independent
of the target hit through the skill's independent-effect callback. This keeps
the target-side action hit-gated while allowing an approved self or ally
benefit to resolve after a miss. New mixed-effect skills must use this metadata
instead of adding skill-name checks to shared resolution code.

The current mixed-effect registrations using this boundary are:

- Crusader Strike;
- Shield of Righteous;
- Heroric Charge;
- Cumbrous Axe; and
- Shield Lash.

The engine records the most recent resolution outcome separately for each
target. Adapters and other consumers must use that authoritative outcome to
distinguish a true evade from a landed attack that happens to deal zero damage.

## Skill Data Requirements

_To be documented._

## Change Log

- 2026-07-26 — Initial document created.
- 2026-07-31 — Documented shared hit-gated target effects, independent
  beneficial callbacks for mixed-effect attacks, and authoritative per-target
  outcomes.
