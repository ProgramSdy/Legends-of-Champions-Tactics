# Legends of Champions Tactics — Battle Victory Conditions and Round-Limit Design Discussion

**Date:** 2026-09-11  
**Status:** Design decision implemented by COMBAT-008. The initial numerical
limits remain subject to later simulation and playtesting balance review.

## 1. Current Battle-End Conditions

The current battle design has two primary termination conditions:

1. **Elimination victory** — if all heroes on one team become unable to continue fighting, the opposing team wins.
2. **Maximum-round termination** — if neither team has been eliminated when the maximum number of rounds is reached, the battle ends and a result must be determined.

Before COMBAT-008, the engine used one general maximum of approximately
**15 rounds**. Live battles now use battle-size-specific completed-round caps.

A round limit is important because low-DPS, high-sustain compositions — for example teams with multiple Priests or Paladins — could otherwise continue healing and prolong a battle excessively.

However, defensive and sustain-oriented play should remain a legitimate strategy. The objective is not to eliminate this archetype, but to define a fair and predictable result when time expires.

## 2. Maximum-Round Result Hierarchy

Two possible timeout criteria were considered: surviving hero count and remaining HP percentage.

The agreed direction is to use them hierarchically.

### First tiebreaker — surviving heroes

When the maximum round is reached:

> **The team with more surviving heroes wins.**

Example:

- Team A: 3 surviving heroes
- Team B: 2 surviving heroes

Team A wins regardless of remaining HP percentages.

The reasoning is that surviving hero count represents battlefield control and action economy. If combat continued, the team with more active heroes generally has additional actions, skills, targeting options, and combination potential.

### Second tiebreaker — remaining HP percentage

Only when both teams have the **same number of surviving heroes** should remaining HP percentage be compared.

```text
Maximum round reached
        ↓
Compare surviving hero count
        ↓
Different? → More surviving heroes wins
        ↓
Equal
        ↓
Compare remaining HP percentage
```

This prevents an unintended case where one full-health survivor could defeat three low-health survivors purely because of HP percentage.

## 3. Exact Tie → Draw

An edge case was discussed where both teams have:

- the same surviving hero count; and
- the same remaining HP percentage.

Example:

- Team A: 1 survivor at 50% HP
- Team B: 1 survivor at 50% HP

### Decision

> **The battle result should be Draw.**

There is no need to invent increasingly obscure tiebreakers merely to force a winner when the meaningful victory measurements are equal.

The proposed hierarchy is therefore:

```text
1. Opposing team eliminated → Win

Otherwise, maximum round reached:

2. More surviving heroes → Win

3. Same survivor count:
   Higher remaining HP percentage → Win

4. Same survivor count and same HP percentage → Draw
```

## 4. PvP Draw Behaviour

For PvP, Draw is a natural and acceptable result.

If both players finish with equal surviving hero count and equal remaining HP percentage, neither has demonstrated superiority according to the defined objectives. The match should therefore be recorded as a Draw rather than arbitrarily awarding victory.

## 5. PvE Draw Behaviour — Battle Result vs Stage Result

PvE requires a distinction between **battle outcome** and **stage progression**.

### Decision

A PvE Draw does **not** clear the stage.

```text
Battle Result: DRAW
Stage Result:  NOT CLEARED
```

The player must replay the encounter to progress.

This does not require the battle itself to be labelled a Loss. The player genuinely achieved a Draw, but did not satisfy the requirement to defeat the stage encounter.

This distinction may also provide useful feedback: a Draw can communicate that the player is close to clearing the encounter.

Future reward design could potentially distinguish Draw from Loss, but no consolation reward was finalized.

## 6. Revival Skills Remain Excluded

The current game intentionally does **not** include revival abilities for Priest, Paladin, or other heroes.

A defeated hero represents a major change in:

- action economy;
- available skills;
- targeting;
- team combinations;
- formation pressure;
- battlefield control.

Revival could therefore become disproportionately valuable and risk making revival-capable heroes near-mandatory selections.

### Current direction

> **Do not introduce revival mechanics unless a robust balancing model is designed first.**

The absence of revival also keeps the surviving-hero timeout rule much clearer.

## 7. Different Maximum Rounds for 1v1, 2v2, and 3v3

The current system uses approximately 15 rounds as a general maximum, but 1v1, 2v2, and 3v3 have substantially different:

- combatant counts;
- action density;
- interaction complexity;
- healing capacity;
- combination opportunities;
- expected battle duration.

The discussion therefore supports making maximum rounds configurable by battle size.

The initial implemented values are:

```text
1v1 → 9 completed rounds
2v2 → 13 completed rounds
3v3 → 15 completed rounds
```

These are active balance values rather than a second source of runtime truth:
the engine-owned mapping in
`game/game.py` is authoritative. They may be tuned later from simulation and
human-playtest evidence without changing the timeout hierarchy.

Conceptually:

- **1v1** should feel shorter and more duel-like.
- **2v2** introduces stronger hero-combination and Interlock play.
- **3v3** is the fullest tactical expression and may require more time for formation, combinations, and evolving battle states.

## 8. Use the Battle Simulator to Determine Final Round Limits

The existing **Battle Simulator** is the appropriate tool for the first empirical tuning pass.

For 1v1, 2v2, and 3v3, simulations should cover many representative hero/team combinations and enough battles to produce useful distributions.

Useful telemetry includes:

- battle size;
- participating heroes/team composition;
- formation;
- round in which battle ended;
- elimination vs maximum-round termination;
- winner;
- surviving hero count;
- remaining HP percentage;
- Draw frequency;
- optionally damage/healing statistics to identify sustain-heavy outliers.

The analysis should answer:

- What is average and median battle length for each battle size?
- By which round have roughly 80%, 90%, or 95% of battles naturally ended?
- What percentage of battles hit the proposed maximum?
- Which compositions disproportionately reach the limit?
- Are sustain-heavy teams producing excessive Draws?
- Does a proposed limit prematurely stop otherwise healthy tactical battles?

A useful process is:

```text
Generate representative matchups
        ↓
Run hundreds/thousands of simulations
        ↓
Record natural battle duration
        ↓
Study the duration distribution
        ↓
Choose provisional maximum-round thresholds
        ↓
Run targeted simulations around those thresholds
```

## 9. Simulation Is Necessary but Not Sufficient

Battle Simulator data can show whether a round limit is mathematically reasonable, but it cannot fully determine whether combat feels enjoyable.

After simulator-based tuning, human playtesting remains necessary.

The simulator answers:

> “How long do battles statistically last?”

Human playtesting answers:

> “Does this battle feel too short, too long, tense, repetitive, or satisfying?”

Final round limits should therefore use:

> **simulation data + human playtesting**

## 10. Consolidated Proposed Victory Logic

```text
BATTLE IN PROGRESS
        │
        ├── One team has no surviving heroes
        │       ↓
        │   Other team WINS
        │
        └── Maximum round reached
                ↓
        Compare surviving hero count
                │
        ┌───────┴────────┐
        │                │
     Different          Equal
        │                │
More survivors      Compare remaining
    WINS             HP percentage
                         │
                  ┌──────┴──────┐
                  │             │
               Different       Equal
                  │             │
             Higher HP        DRAW
                WINS
```

For PvE:

```text
WIN  → Stage Cleared
LOSS → Stage Not Cleared
DRAW → Stage Not Cleared
```

For PvP:

```text
WIN / LOSS / DRAW
```

## 11. Design Principles Reinforced

- Elimination remains the clearest victory.
- Defensive/healing strategies remain legitimate.
- A round limit prevents indefinite sustain battles.
- Surviving hero count is the strongest timeout indicator of battlefield advantage.
- HP percentage resolves otherwise equal surviving-force situations.
- Genuine equality produces Draw rather than an arbitrary winner.
- PvE battle result and stage progression are separate concepts.
- Maximum-round limits should likely depend on battle size.
- Final limits should be validated through Battle Simulator data and human playtesting.

> **A player should understand exactly why the battle ended and why the system awarded the result it did.**

Victory conditions should be predictable enough that players can deliberately plan around them as part of the tactical game.
