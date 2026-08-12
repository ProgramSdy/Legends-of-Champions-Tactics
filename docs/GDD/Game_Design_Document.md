# Game Design Document

## Status and Authority

This document records the implemented gameplay baseline as of 2026-08-06. It
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
   enemy control mode, and optionally a seed.
3. Create a battle; Python constructs the combatants and begins round flow.
4. On a player-controlled turn, choose a legal skill and its legal targets.
5. Observe authoritative events, update strategy around status/cooldown/turn
   state, and continue until victory, defeat, draw, or round limit.

Warrior's Barrack is also available as a temporary structured training location.
It offers three fixed practice battles with a four-definition starting player
selection (Warrior Weapon Master, Mage Comprehensiveness, Priest
Comprehensiveness, and Rogue Comprehensiveness). Its sequence is not profile
progression: no unlocks, rewards, persistence, or recovery are implemented.
Friendly victories advance its current client-memory battle; defeat, draw, and
round limit retry that same battle.

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

## Design Pillars Evidenced by the Current Build

- **Tactical turn pressure:** current agility establishes round initiative and
  can be changed by effects.
- **Skill-kit decisions:** heroes use specialization-defined skills with target
  rules, cooldowns, casting behavior, and effects.
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

The current temporary Warrior's Barrack training sequence uses the existing
live 2v2, 1v1, and 3v3 formats with predefined computer enemy teams. It does
not add a gameplay rule, engine mode, campaign system, or persistent
progression model.

## Progression and Meta-Game

No XP, levels, equipment, inventory, rarity, unlock system, campaign, account,
save progression, or resource/mana economy is currently implemented or
approved. Battle-local stat and status changes are not persistent progression.

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

- 2026-08-06 — Rebuilt from the current engine, adapter, and web/API baseline;
  unapproved product decisions are explicitly recorded as open.
- 2026-08-10 — Recorded the implemented temporary Warrior's Barrack structured
  training scope and explicitly excluded it from progression/persistence.
