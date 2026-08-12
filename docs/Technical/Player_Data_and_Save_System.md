# Player Data and Save System

## Purpose

Authoritative technical design for future persistent player data, local storage,
save/load behaviour, active-battle recovery, and abandonment in **Legends of
Champions Tactics**. This document records agreed design principles; it does
not describe an implemented persistence system.

The present adapter/session registry is process-local and non-persistent. The
agreed design below replaces neither current battle authority nor existing
versioned battle contracts until an explicitly authorised implementation task
does so.

## Authority and Scope

- Python/backend is authoritative for player progression, persistent player
  data, active battle state, save/checkpoint decisions, and recovery.
- React is a client. It may request an operation and render returned state, but
  must not directly write or reconstruct persistent player data.
- The preferred initial local persistence direction is SQLite. The data model
  must allow a future migration to online accounts, server storage, and PvP
  without redefining player-progression concepts.
- SQLite, schemas, migrations, authentication, online accounts, cloud sync,
  and PvP persistence are not implemented or designed in detail by this
  document.

## Data Domains

The following domains must remain separate even when stored together.

### Static Game Data

Static game data is product/engine content, not player ownership or save data.
Examples include:

- hero definitions, faculties, specializations, skills, and status metadata;
- stage definitions and training/challenge definitions; and
- gameplay rules and balance data.

### Persistent Player Data

Persistent player data belongs to a stable player/profile identity. Initial
data must include at least:

- a stable player/profile ID independent of the display name;
- player/display name;
- unlocked heroes;
- stage and training progress;
- completed stages and challenges;
- relevant player preferences; and
- a reference to active/incomplete battle information when one exists.

### Battle/Session Data

Battle/session data describes one live or recoverable battle, not permanent
ownership or progression. It includes at least:

- selected teams and battle configuration;
- current HP, statuses, cooldowns, turn/round, current actor, and other
  authoritative combat state needed to resume;
- stable definition and combatant IDs required to reconstruct that state; and
- RNG state whenever deterministic continuation requires it.

### Required Separation

These are distinct concepts:

1. A **hero definition** is static game content.
2. A player's **ownership/unlock** of that definition is persistent player
   progression.
3. Selecting the definition into a **particular battle team** is battle/session
   state.

No layer may treat a battle selection as an unlock, or treat a static definition
as proof that a profile owns/unlocked it.

## Initial Persistence Model

The initial implementation should use a lightweight local SQLite database with
clear boundaries between profile/progression records and active-battle
checkpoints. Storage details such as exact table names, keys, indexes, and
migrations are intentionally deferred to the implementation task.

The model must support:

- multiple local profiles with stable IDs and independently editable display
  names;
- one selected active profile for the local play session;
- player-specific unlock/progress/preferences records; and
- zero or one recoverable unfinished PvE/training battle per active profile,
  unless a later design explicitly allows more.

An active battle is a checkpointed authoritative record, not a browser cache.
The database must retain enough versioned data to reject or migrate an
incompatible saved state safely rather than silently producing a different
battle.

## Save and Checkpoint Behaviour

### Permanent Progression

Save persistent progression immediately after it successfully changes. Examples
include stage completion, hero unlocks, and other permanent progression
rewards. A client-visible success must not be reported before the authoritative
backend has committed the corresponding persistent change.

### Active PvE and Training Battles

At battle start, the backend creates and saves an active-battle record linked to
the selected player profile.

After every authoritative stable action/turn, the backend saves or checkpoints
the resulting battle state. The checkpoint occurs only after Python has
successfully resolved the action and reached a stable authoritative state; the
browser must not be responsible for saving after an animation, timeout, refresh,
or unload event.

Each active-battle checkpoint must preserve the information needed to resume
correctly, including the authoritative battle state and RNG state required for
deterministic continuation. It must also retain enough context to present an
unfinished-battle summary, such as stage/training identity and current
round/turn.

Accidentally closing or refreshing the browser must not normally destroy an
active PvE/training battle. On recovery, the backend loads the saved
authoritative state and the client resumes from it; the client does not replay
or invent state from a stale UI snapshot.

### Battle Completion

After an authoritative battle completion, the backend must:

1. record the result;
2. update stage progression;
3. apply any applicable hero unlocks or rewards;
4. persist the updated player profile; and
5. mark completed or remove the active unfinished-battle record as appropriate.

The completion/progression update and active-battle finalisation should be
designed as one reliable backend operation so a crash cannot award completion
while leaving a resumable unfinished battle for the same result.

## Load and Recovery Behaviour

Loading a profile restores its persistent player data and determines whether it
has an active unfinished PvE/training battle.

- With no unfinished battle, the profile enters the Stage Map.
- With an unfinished battle, the UI presents the profile's saved-battle summary
  and lets the player resume or abandon it. The navigation details are
  authoritative in [Screen Flow](../web-ui/Screen_Flow.md).
- Resume loads the saved authoritative battle state and returns directly to the
  Battle page. It must continue from the saved state, not create a new battle.

## Abandonment

A player may explicitly abandon an unfinished PvE/training battle.

When abandonment is confirmed, the backend must remove or end that active
battle and return the player to the Stage Map. It must not award completion or
unlock rewards from the abandoned battle, and it must not remove permanent
progress earned before that battle began.

The UI must require confirmation before destructive abandonment. The browser
does not decide rewards, active-battle deletion, or progression preservation.

Future PvP disconnect, reconnect, timeout, and forfeit policy is intentionally
out of scope and requires a separate design.

## Versioning, Integrity, and Migration Principles

- Persist version information for saved player and battle records so compatible
  changes can migrate deliberately and incompatible saves can be handled
  clearly.
- Preserve stable profile IDs, hero definition IDs, stage IDs, and battle
  identity keys; display names are not durable identity.
- Save only backend-authoritative state. Client preferences may be persisted as
  player data, but never treated as combat authority.
- Design database access behind backend interfaces so moving from local SQLite
  to server-backed storage does not force a redesign of profile, progression,
  ownership, or active-battle concepts.
- Define concrete corruption, failed-write, backup, conflict, and migration UX
  only when implementation is authorised. Until then, implementation must fail
  safely and must not silently discard authoritative progress.

## Open Design Questions

- Exact default starting heroes, starting stage/training progress, and unlock
  rewards.
- Exact player preference fields and profile rename/delete behaviour.
- Whether local profiles have a configurable maximum.
- Active-battle retention, database backup/export, corruption recovery, and
  detailed migration policy.
- The future online-account, cloud-sync, and PvP persistence model.

## Related Documents

- [Screen Flow](../web-ui/Screen_Flow.md) — agreed startup/profile, resume, and
  abandonment navigation design.
- `Architecture.md` — high-level system ownership when expanded.
- `../GDD/Hero_System.md` — hero identity and ownership/progression boundaries.

## Change Log

- 2026-08-10 — Renamed from `Save_System.md`; documented agreed player-data,
  SQLite-direction, backend-authoritative autosave/recovery, completion, and
  abandonment principles. No persistence implementation was added.
