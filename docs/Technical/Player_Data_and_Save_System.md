# Player Data and Save System

## Purpose

Authoritative technical design for persistent player data, local storage,
save/load behaviour, active-battle recovery, and abandonment in **Legends of
Champions Tactics**. UI-021 implements exactly five local save slots around the
UI-020 training progression; the broader design remains deferred.

The battle/session registry remains process-local and non-persistent. SQLite
persists each occupied slot's stable profile identity, timestamps, unlocks,
stage progress, and generic reward counts; it does not checkpoint live battles.

## Authority and Scope

- Python/backend is authoritative for player progression, persistent player
  data, active battle state, save/checkpoint decisions, and recovery.
- React is a client. It may request an operation and render returned state, but
  must not directly write or reconstruct persistent player data.
- The preferred initial local persistence direction is SQLite. The data model
  must allow a future migration to online accounts, server storage, and PvP
  without redefining player-progression concepts.
- The implemented store uses SQLite schema version 2 and stable slots 1–5. The
  backend alone owns the active slot. Fresh databases start with five empty
  slots and no active profile.
- Schema-v1 `profile.local.default` data migrates transactionally into slot 1,
  retaining its profile ID and exact earned state. The schema marker changes in
  the same `BEGIN IMMEDIATE` transaction, so restart cannot duplicate it. An
  impossible/failed migration is retryable and never resets the legacy record.
- Profile names/settings/deletion, authentication, cloud sync, PvP, active
  battle checkpoints, and migration between account systems remain deferred.

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

The implemented local store contains a schema marker, five slot rows, one
backend-owned active-slot reference, occupied-slot profile identities and
creation/last-played timestamps, unlocked definitions, stage state, rewards,
and completion receipts scoped by profile and battle session. `BEGIN IMMEDIATE`
makes each slot initialization/overwrite, active selection, or victory
receipt/progress/reward change atomic.

New slots start with exactly Warrior Weapon Master, Mage Comprehensiveness,
Priest Comprehensiveness, and Rogue Comprehensiveness, zero stage progress, and
no rewards. Confirmed overwrite replaces only the named occupied slot with a
new stable profile identity and fresh state in one transaction. Cancelling or
withholding confirmation makes no write.

## Save and Checkpoint Behaviour

### Permanent Progression

Save persistent progression immediately after it successfully changes. Examples
include stage completion, hero unlocks, and other permanent progression
rewards. A client-visible success must not be reported before the authoritative
backend has committed the corresponding persistent change.

### Active PvE and Training Battles (Deferred)

UI-021 does not save active battles. At battle start, the backend creates an
in-memory battle session only; a refresh/restart cannot resume it and grants no
progress until a completion transaction succeeds. Structured sessions retain
the active profile identity from launch; completion after a slot switch is
rejected instead of leaking a result into the new active slot.


### Battle Completion

After an authoritative friendly structured-battle victory, the completion route
records a durable receipt, updates the stage, applies a permitted unlock or
generic item-card reward, and returns the updated profile in one transaction.
The receipt makes reload/retry/replay calls idempotent. It does not save or
finalize an active-battle checkpoint because active-battle recovery is deferred.

## Load and Recovery Behaviour

Listing always returns five summaries. Loading an occupied slot atomically
selects it, updates last-played metadata, and returns its progression. Empty or
out-of-range loads are rejected. With no active selection, progression,
roster-gated battle creation, structured stages, and completion return a typed
conflict rather than selecting a fallback. Active unfinished-battle recovery,
automatic backup/repair, and cloud recovery remain unimplemented.

## Abandonment (Deferred)

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

- Exact player preference fields and profile rename/delete behaviour.
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
- 2026-08-19 — Implemented the limited default-profile SQLite progression
  store for UI-020 training rewards; profiles, inventory, and battle recovery
  remain deferred.
- 2026-08-20 — Upgraded to schema version 2 with five isolated slots,
  backend-owned active selection, safe UI-020 migration, and confirmed
  transactional overwrite.
