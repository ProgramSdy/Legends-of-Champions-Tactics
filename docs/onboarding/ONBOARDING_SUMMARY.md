# Onboarding Summary

## Executive understanding

Legends of Champions Tactics is a two-team, round-based hero combat foundation.
A roster combines eight faculties and concrete specializations, generally with
three skills each. Heroes act in descending agility order and use attacks,
heals, control, delayed spells, stacking effects, resistances, and summoned
units. A Pygame interface supports keyboard-driven local play, while automated
drivers reuse the same battle objects for matchup and tournament simulation.

The engine is centred on `Game`, `Hero`, and `Skill`. `Game` advances five
states; `Hero` holds nearly all combatant state and chooses actions; `Skill`
filters targets and dispatches to bound specialization methods. Status
application and resolution span hero methods, `Skill.execute`,
`StatusEffectManager`, and `StatusDispell`. Balance ranges live in Excel.

This review describes commit `f88fbb92`, tagged `v0.1-foundation`.

## Five most important architectural observations

1. **One rule path serves manual and simulated combat.** Both modes advance the
   same `Game` state machine and invoke the same hero/skill effects
   (`main.py:79-105`; `simulation_engine.py:42-60`).
2. **The domain model is highly stateful and cyclic.** `Game` owns heroes;
   heroes point back to `Game` and the interface; skills point to initiators and
   bound hero methods; summons point to masters.
3. **A skill is implemented across several modules.** Generic execution and
   name-specific exceptions are in `skills/skill.py`, calculations/application
   in faculty modules, persistent fields in `Hero`, and round processing in the
   status manager.
4. **Presentation and authority are interleaved.** Rules emit ANSI prose, sleep,
   and call Pygame observers directly; initialization loads graphics even for
   simulations.
5. **The engine has an explicit step-able lifecycle but no external contract.**
   No command schema, event schema, snapshot serialization, replay seed, or
   networking boundary exists yet.

## Five strongest parts

1. The state-machine lifecycle is visible and small enough to trace.
2. Automated simulations exercise the real battle logic rather than a separate
   approximation.
3. Faculty/specialization inheritance makes roster organization and skill kits
   discoverable.
4. Central hit resolution consistently considers death, evasion, immunity,
   target cardinality, and casting interruption.
5. Core statistics and resistance ranges are externally tunable, and summons
   reuse normal hero/turn machinery.

## Five largest technical risks

1. **Status consistency:** dozens of synchronized flags, counters, records, and
   hard-coded string branches make partial cleanup and interaction defects
   likely (`heroes/hero.py:25-281`;
   `game/status_effect_manager.py:19-987`).
2. **Circular imports/global wildcard imports:** package initialization order
   connects `heroes`, `skills`, and `game` and makes dependencies implicit.
3. **Client coupling:** Pygame surfaces, blocking input/sleeps, formatted text,
   and direct UI callbacks sit inside or next to authoritative execution.
4. **Non-determinism without replay:** unseeded randomness affects
   construction, AI, targeting, damage, grouping, and tournaments.
5. **Insufficient regression evidence:** the three `test*` files are UI
   experiments; no assertion-based rules suite, CI, or persisted balance
   baseline was found.

## Five most important questions for the repository owner

1. Which current behaviors—including known summon/status edge cases—are
   canonical rules that future tests must preserve?
2. What process boundary is intended between Python and Godot?
3. Must battle execution be deterministic/replayable, especially for online
   multiplayer and balance comparison?
4. Which specializations are in the supported roster, and why do generator and
   simulator lists differ?
5. Are the Excel files production runtime data, designer workbooks, or both,
   and how should changes be validated?

## Recommended next analysis steps

These are analysis activities, not restructuring proposals:

1. Establish owner-approved, example-based expected outcomes for battle phase
   ordering, durations, control, casting, dispels, summons, and round-cap draws.
2. Build a behavior inventory mapping every concrete skill to its constructor,
   `Skill.execute` special cases, hero method, status fields, tick/expiry logic,
   and dispel classification.
3. Run seeded observational experiments (without changing production code) for
   representative specializations and record reproducibility gaps and
   invariants.
4. Catalogue the exact state read by `GameInterface` and the messages emitted by
   the engine to define the facts a future client boundary would need.
5. Agree on supported roster/data/platform scope, then use it to define a
   regression matrix and balance baseline.

## Validation snapshot

- All 44 repository Python files parsed successfully with `ast.parse`.
- A headless `Warrior_Comprehensiveness` versus `Mage_Comprehensiveness`
  simulation completed successfully in eight state transitions (round 2,
  Group B surviving).
- This is smoke validation only. The repository contains no discovered
  assertion-based automated test suite.

## Confidence ratings

| Area | Confidence | Supporting evidence | Why not higher |
|---|---:|---|---|
| Overall project | 91% | Entire tracked game tree, history/tag, notes, workbooks, deck, assets, dependencies, and entry points inspected | Product intent and canonical-versus-prototype behavior require owner confirmation |
| Battle flow | 95% | Full `Game` lifecycle and every external dispatcher traced; smoke battle executed | Edge interactions can re-enter display/status/death paths, and no formal expected traces exist |
| Hero architecture | 94% | Base class, all faculty/specialization constructors, generator, and inheritance map inspected | Some subclasses are omitted inconsistently from generator/simulator catalogues |
| Skill system | 90% | `Skill` pipeline and all concrete skill registrations/method locations inspected | Individual rules are numerous and split across name-specific branches; not every random outcome was executed |
| Buff/debuff system | 84% | All status flags/categories, full manager, dispeller, and representative application sites inspected | Roughly 70 bespoke statuses and cross-status branches lack regression fixtures; intent of some classifications is uncertain |
| AI | 87% | Default selection/targeting and every specialization override/strategy method located and traced | Many classes use inherited random behavior; strategy quality and intended weights are undocumented |
| Summoning | 89% | Factory, five concrete units, master links, queue insertion, expiry, and death paths inspected | Known developer-note defects and complex master/summon edge cases were not exhaustively reproduced |
| Tournament simulator | 93% | Active 1v1, 2v2 group/knockout, and 3v3 flows traced end to end | Intended tie/seeding/fairness rules are undocumented; full tournament was not run due combinatorial scope |
| Balance simulation | 86% | Pairing/team generation, repeated battle aggregation, data inputs, and outputs inspected | No acceptance thresholds, persisted results, seeds, or statistical methodology exist |
| Future Godot readiness | 82% | Domain/UI dependencies, execution stepping, data loading, messages, and absence of protocol/serialization/networking verified | The intended deployment model and client/server contract have not been chosen |

**Overall confidence:** 90%. The main execution architecture and implemented
systems are clear. Confidence is constrained primarily by undocumented design
intent, known edge-case defects, and the absence of behavioral tests—not by an
  inability to locate the current code paths.
