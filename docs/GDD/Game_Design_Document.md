# Game Design Document

## Status and Authority

This document records the implemented gameplay baseline as of 2026-08-15. It
does not approve unimplemented progression, economy, campaign, or online
features. When current engine behavior and a future owner decision differ, the
owner decision takes priority and this document must be updated deliberately.

## Current Product Definition

Legends of Champions Tactics is a round-based, two-side tactical hero battle.
Players configure teams, choose legal skills and targets, and manage initiative,
cooldowns, casting, control, statuses, healing, and summons. Python resolves
all gameplay outcomes; the web client and local Pygame interface present those
outcomes.

## Current Player Loop

1. Open the startup title scene and enter the Team Builder.
2. Choose a 1v1, 2v2, or 3v3 battle, player heroes, enemy composition mode,
   enemy control mode, and optionally a seed. In 2v2 and 3v3, choose an
   approved friendly formation; a player-controlled enemy also chooses its
   formation, while Python chooses the computer enemy's formation.
3. Create a battle; Python constructs the combatants and begins round flow.
4. On a player-controlled turn, choose a legal skill and its legal targets.
5. Observe authoritative events, update strategy around status/cooldown/turn
   state, and continue until victory, defeat, draw, or round limit.

The Stage Map also offers two backend-authoritative structured training stages:
Paladin's Altar and Warrior's Barrack. Each has nine fixed battles with an
ordered predefined computer enemy team and fixed enemy formation. In 2v2 and
3v3, the player chooses a size-valid friendly formation; 1v1 has no formation
selection. The player can choose only heroes currently unlocked for the stable
local profile. Friendly victory is the only progression trigger; defeat, draw,
and round limit retry the same battle. A completed step unlocks only the next
step in its own stage.

## Supported Playable Scope

The current web/API roster contains ten approved definitions: Priest
Comprehensiveness and Discipline; Paladin Retribution, Protection, and Holy;
Mage Comprehensiveness; Warrior Defence, Weapon Master, and Berserker; and
Rogue Comprehensiveness. This is not the full legacy engine catalogue.

The legacy engine contains additional faculty/specialization classes, while
its generator and simulation tooling expose different subsets. They are
implementation coverage differences, not an approved expansion of the web
roster. Repeated definitions and cross-team overlap are permitted for player
and specified-enemy teams; random enemy composition samples without replacement.

## Battle Formations

Formations are an implemented tactical setup feature for 2v2 and 3v3 only.
They assign each ordered hero a battle position of `front` or `rear`; Python is
authoritative for this state, legal targets, computer targeting, and applicable
damage adjustments. The web client presents the returned formation and
positions but does not calculate them.

| Battle size | Formation | Ordered positions |
|---|---|---|
| 2v2 | Front and Rear (`front-rear`) | front, rear |
| 2v2 | Side by Side (`side-by-side`) | front, front |
| 3v3 | One Front, Two Rear (`one-front-two-rear`) | front, rear, rear |
| 3v3 | Two Front, One Rear (`two-front-one-rear`) | front, front, rear |
| 3v3 | All Front (`all-front`) | front, front, front |

In either size, the friendly formation is selected before battle. A
player-controlled enemy uses an explicitly selected formation; a
computer-controlled enemy receives a formation selected by the adapter from
the seeded battle random stream. One-versus-one has no formation input.

Formation positions matter to the currently authorized Warrior Weapon Master,
Warrior Defence, Warrior Berserker, Mage Comprehensiveness, Paladin
Retribution, Paladin Protection, Paladin Holy, Priest Comprehensiveness, and
Priest Discipline skills that carry an owner-approved attack type. The expanded
Paladin/Priest classifications are limited to Hammer of Anger, Crusader Strike,
Hammer of Revenge, Shield of Righteous, Heroric Charge, Holy Blast, Holy Smite,
Shadow Word Pain, Penance's opponent branch, and Holy Word Punishment. Melee
cannot target a rear defender while any front defender is alive, and approved
position damage adjustments are applied once by Python. Other skills do not
receive inferred attack types. See `Combat_System.md` for the exact rules.

## Design Pillars Evidenced by the Current Build

- **Tactical turn pressure:** current agility establishes round initiative and
  can be changed by effects.
- **Skill-kit decisions:** heroes use specialization-defined skills with target
  rules, cooldowns, casting behavior, and effects.
- **Formation choices:** 2v2 and 3v3 team ordering and formation determine
  front/rear combat positions before battle begins; presentation preserves the
  selected formation without becoming a separate client-side rule.
- **Per-target resolution:** multi-target attacks resolve evasion, immunity,
  hit, damage, and harmful on-hit effects independently.
- **Persistent combat state:** buffs, debuffs, control, damage-over-time,
  healing-over-time, and summons change later turns as well as the current one.
- **Authoritative resolution:** UI presentation, logs, and animations do not
  decide legal actions or battle outcomes.

## Battle Session and Outcome

One surviving group wins. If no group survives, the result is a draw. The
engine also stops at its configured round cap; the current implementation
reports that as an unresolved round-limit outcome without selecting a winner.
See `Combat_System.md` for the exact lifecycle and its implementation caveat.

## Content Model

- **Faculty:** broad engine archetype, such as Warrior or Mage.
- **Specialization:** public/API term for the engine's `major` field.
- **Hero:** a battle-local combatant with generated attributes, skills, state,
  allies/opponents, and a side/group.
- **Skill:** a specialization-defined action with target and effect metadata.
- **Status:** battle-local flags, counters, and records that modify behavior.
- **Summon:** a hero-derived combatant linked to a master and duration.

## Modes and Tooling Boundaries

The web client supports configured live 1v1, 2v2, and 3v3 sessions. Pygame is
a local legacy interface, and simulation paths are engineering/balance tools;
neither independently establishes product rules. API sessions can use a seed
for reproducible session randomness. Direct legacy/simulation execution has no
equivalent recorded replay contract.

Paladin's Altar and Warrior's Barrack use the existing 1v1, 2v2, and 3v3
combat formats with predefined computer enemy teams and fixed enemy formations.
Their 2v2 and 3v3 friendly formations remain player-selected; 1v1 has none.
They do not add combat rules or a campaign system. Their completion only
changes the minimal persisted training progression described below.

## Progression and Meta-Game

UI-021 stores local progression in exactly five backend-owned save slots. A
new slot starts with exactly Warrior Weapon Master, Mage Comprehensiveness,
Priest Comprehensiveness, and Rogue Comprehensiveness. Paladin Protection,
Paladin Retribution, Paladin Holy, Warrior Berserker, Warrior Defence, and
Priest Discipline start unavailable to player selection. The implemented
training rewards unlock only the named Paladin and Warrior definitions; Priest
Discipline deliberately remains locked until a future owner-designed Priest
stage supplies her reward. Fixed structured enemies remain independent of
player ownership.
Warrior's Barrack Battle 6 grants the single persistent generic reward ID
`reward.item-card.basic`; it has no art, combat effect, inventory, equipment,
economy, or item name. The backend persists each first friendly-victory reward
atomically with the stage update and exposes availability to the UI. XP, levels,
attributes, inventory/equipment, campaign, accounts, cloud sync, and active
battle recovery remain unimplemented.

## Open Product Decisions

- Canonical release roster and expansion policy.
- Product audience, platform, and long-term game vision.
- Progression, economy, campaign, and online/matchmaking model.
- Balance targets, ownership of Excel balance data, and acceptance thresholds.
- Canonical round-cap/tiebreak and initiative-tie rules.

## Related Documents

- `Combat_System.md`
- `Hero_System.md`
- `Skill_System.md`

## Change Log

- 2026-08-15 — Added the implemented 2v2/3v3 formation milestone, including
  size-specific pre-battle selection and Python-owned Warrior position rules.
- 2026-08-19 — Replaced the temporary Warrior's Barrack sequence with the two
  persisted nine-battle training stages and their limited unlock/item rewards.
- 2026-08-20 — Added five isolated local save slots and the exact four-hero
  new-game roster without changing the training curricula.
- 2026-08-06 — Rebuilt from the current engine, adapter, and web/API baseline;
  unapproved product decisions are explicitly recorded as open.
- 2026-08-10 — Recorded the then-temporary Warrior's Barrack structured
  training scope; superseded by the persisted UI-020 training slice.
