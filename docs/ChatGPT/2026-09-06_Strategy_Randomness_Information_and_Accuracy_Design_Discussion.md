# Legends of Champions Tactics — Strategy, Randomness, Information, and Accuracy Design Discussion

**Date:** 2026-09-06  
**Purpose:** Summary of the game-design discussion. This records design direction; unresolved mechanics should not be treated as implementation specifications.

## 1. Core Strategic Philosophy

The discussion reaffirmed the central philosophy of *Legends of Champions Tactics*:

- Battles should be won primarily through **planning, understanding, and execution**, not luck.
- No hero should be designed as a universally stronger choice.
- Each hero should have distinctive strategic value.
- New heroes should expand viable combinations rather than obsolete existing heroes.
- Mastery should come from understanding relationships between heroes, formations, skills, states, timing, and counterplay.

The current game already contains substantial strategic depth through:

1. **Hero knowledge** — attributes, skills, strengths, and limitations.
2. **Team composition** — choosing heroes whose abilities complement one another or answer the opponent.
3. **Formation** — 1v1, 2v2, and 3v3 arrangements, including side-by-side, front/rear, two-front-one-rear, and one-front-two-rear.
4. **Skill choice and timing** — choosing the correct action and target at the correct moment.
5. **Interlocking effects** — skills and attached states interact, creating combinations, counters, and changing battle states.

### Conclusion

The game does not currently need additional complexity merely to become “more strategic.” A more important challenge is making the existing strategic depth visible, understandable, and enjoyable.

## 2. Discovery and Making Strategy Visible

An important concept is the player's discovery moment:

> “Oh — I didn't realize I could use these mechanics together like that.”

The goal is not necessarily to add more systems, but to help players discover relationships that already exist.

The Interlock/state system is particularly important. If interactions exist only inside long skill descriptions, many players may never recognize them.

Future UI/UX should therefore help players learn through play, potentially using:

- useful skill tooltips;
- clear status-effect information;
- visible interaction/counter information;
- contextual information while choosing skills and targets;
- small visual indicators for relevant interactions where appropriate.

**Principle:** Strategic depth only creates value when players can perceive, understand, and act on it.

## 3. Mid-Battle Random Card Mechanic — Rejected for Now

A possible system was considered in which both teams would receive random card choices at selected rounds, for example around rounds 3, 7, and 11 in a battle with an approximately 15-round maximum.

A player might choose one card from three to five options, with effects such as:

- restoring HP;
- applying a beneficial state;
- poisoning an opponent;
- applying another temporary battle effect.

### Potential benefit

This could create uncertainty and provide a disadvantaged team with a comeback opportunity.

### Fundamental problem

It could undermine the game's central philosophy. A player could build the better team, choose the better formation, understand the matchup, and execute correctly, but still lose because the opponent received a particularly favourable random card.

The emotional interpretation changes from:

> “My opponent planned or played better.”

to:

> “The random system changed the result.”

### Decision

**Do not introduce the random mid-battle card system at this stage.**

Comebacks should preferably emerge from better tactical decisions, timing, target selection, skill combinations, status manipulation, and other understandable player-controlled mechanisms.

The desired comeback is:

> “I found a better line of play.”

rather than:

> “I drew the right random effect.”

## 4. Randomness Is Not Automatically Bad

The discussion distinguished **uncontrolled randomness** from **informed risk**.

The game already contains randomness in skill damage. Skills generally deal damage within a range rather than one perfectly fixed value.

Example:

- Enemy HP: 20
- Possible skill damage: 15–25

The player understands that the attack may kill the target but is not guaranteed to do so. The player can deliberately decide whether the risk is acceptable.

**Principle:** Randomness can serve strategy when the player understands the probability or range before making the decision and voluntarily accepts the risk.

This differs from an unexpected random event that overrides a carefully planned battle.

## 5. Battle Information Transparency

Pokémon and *Super Robot Wars* were discussed as contrasting approaches.

Pokémon often leaves detailed expected damage/hit calculations less explicit to ordinary players, while tactical games such as *Super Robot Wars* more directly surface decision-relevant combat information before an attack.

For *Legends of Champions Tactics*, greater tactical transparency better fits the emphasis on informed decision-making.

When a player selects a skill and target, the game should eventually consider presenting:

- expected damage range;
- final hit chance;
- relevant status interactions;
- other important consequences when they materially affect the decision.

Example:

```text
FATAL STRIKE
Damage:      18–29
Hit Chance:     61%
Target HP:      21
```

Compared with:

```text
QUICK STRIKE
Damage:      12–17
Hit Chance:     91%
Target HP:      21
```

This creates an understandable decision: pursue a higher-risk kill or choose the more reliable action.

The objective is **not** to expose every internal calculation. The UI should expose enough information to support meaningful decisions without turning combat into an unreadable mathematical worksheet.

## 6. Traditional Random Critical Hits — Do Not Add for Now

Traditional critical-hit systems were discussed, such as a random percentage chance to deal 1.5× or 2× damage.

### Decision

**Do not add a conventional random critical-hit mechanic at this stage.**

A random critical can create a large outcome swing that the player did not intentionally create.

If the game needs “critical-like” high-damage moments, a more suitable approach is to create them through conditions and interactions, for example:

- increased damage against a Bleeding target;
- powerful attacks enabled by specific states;
- abilities whose payoff requires preparation;
- combinations created by another hero.

**Principle:** High-impact outcomes should preferably be earned through setup and interaction rather than awarded by an unrelated random critical roll.

## 7. Accuracy and Evasion

The current design was described as having no separate skill Accuracy property. Hit chance is effectively influenced by target Evasion, which is related to Agility; agile classes such as Rogue therefore naturally have higher evasion.

The discussion identified useful design space in introducing Accuracy.

### Proposed conceptual model

Each major class can have a **Base/Class Accuracy**, while individual skills can have an **Accuracy Modifier**.

```text
Final Hit Chance
=
Class Base Accuracy
+ Skill Accuracy Modifier
- Target Evasion
+ Relevant State / Other Modifiers
```

Example:

```text
Warrior Base Accuracy      90%
Fatal Strike Modifier     -15%
Target Rogue Evasion       20%

Final Hit Chance = 55%
```

The concepts have separate responsibilities:

- **Class Base Accuracy** — general reliability/precision identity of the class.
- **Skill Accuracy Modifier** — how easy or difficult the particular technique is to land.
- **Evasion** — how difficult the target is to hit.

This supports deliberate trade-offs: a powerful attack can be less reliable, while a lower-damage attack can be safer.

### Balancing caution

Class Accuracy differences should probably remain moderate. Excessive class-level differences could create frustrating hard counters where one class simply cannot hit another reliably.

The larger tactical variation may be better expressed at skill level, while class accuracy provides a smaller identity/tendency.

Exact values and hit-chance caps/floors were **not finalized** and require later design and playtesting.

## 8. Accuracy as Part of the Interlock System

A promising direction is allowing Accuracy and Evasion to interact with the existing state system.

Illustrative possibilities:

```text
Blinded → Accuracy reduced
Marked → Attacks against this target gain Accuracy
Frozen → Evasion reduced
Paralyzed → Evasion heavily reduced or otherwise restricted
```

These are examples, not finalized effects.

The important idea is that Accuracy should not become an isolated stat system. It can participate in the existing interlocking battle-state philosophy.

Example:

```text
Rogue applies Mark
        ↓
Target becomes easier to hit
        ↓
Warrior uses a powerful but normally inaccurate skill
        ↓
Prepared interaction increases reliability
```

The player has created reliability through planning and team interaction.

## 9. Accuracy Questions Still to Resolve

Before implementation, explicitly decide:

1. Do physical and magical attacks use the same Accuracy model?
2. Can direct-damage spells miss?
3. Do hostile Debuffs and control skills require hit checks?
4. Do healing skills require Accuracy?
5. Can friendly Buffs miss?
6. Do self-targeted abilities ever require Accuracy?
7. How should multi-hit abilities calculate Accuracy?
8. Should certain abilities be explicitly guaranteed to hit?
9. What should minimum and maximum final hit chances be?
10. How should Accuracy/Evasion-changing states interact with the existing Interlock system?

These boundaries should be settled before asking Codex to implement Accuracy.

## 10. Overall Direction

### Randomness that weakens the game's identity

- random comeback cards capable of overturning strategic preparation;
- traditional unrelated random critical hits;
- major hidden outcome swings the player could not reasonably evaluate.

### Controlled uncertainty that can strengthen the game

- visible damage ranges;
- visible hit probability;
- deliberate high-risk/high-reward skills;
- Accuracy/Evasion trade-offs;
- state interactions that modify reliability;
- tactical setup that converts a risky action into a more reliable one.

> **Legends of Champions Tactics should not eliminate uncertainty. It should make uncertainty understandable, strategically manageable, and something the player deliberately chooses to engage with.**

The intended player journey is:

**plan the team → choose the formation → understand interactions → read the battle state → evaluate risk → execute the plan.**

Victory should primarily feel like the consequence of better understanding and better decisions.
