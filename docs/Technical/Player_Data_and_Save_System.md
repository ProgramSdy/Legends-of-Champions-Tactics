# Player Data and Save System

## Purpose

Authoritative technical design for persistent player data, local storage,
save/load behaviour, active-battle recovery, and abandonment in **Legends of
Champions Tactics**. Development retains the UI-023 five local save slots;
RELEASE-002 Batch 1 adds a separate Public player-owned save foundation;
Batch 2 adds an isolated, default-off Public battle lifecycle and durable
terminal receipts without making live battles resumable.

The battle/session registry remains process-local and non-persistent. SQLite
persists each occupied slot's stable profile identity, timestamps, unlocks,
stage progress, generic reward counts, and Arena Run data; it does not
checkpoint live battles.

## Authority and Scope

- Python/backend is authoritative for player progression, persistent player
  data, active battle state, save/checkpoint decisions, and recovery.
- React is a client. It may request an operation and render returned state, but
  must not directly write or reconstruct persistent player data.
- The preferred initial local persistence direction is SQLite. The data model
  must allow a future migration to online accounts, server storage, and PvP
  without redefining player-progression concepts.
- The Development store uses SQLite schema version 4 and stable anonymous slots
  1–5. Public uses a separate schema-v5 database with five slots **per Player
  ID** and a player-scoped active slot. Both start with empty slots and no
  active profile; neither imports the other's data.
- Schema-v1 `profile.local.default` data migrates transactionally into slot 1,
  retaining its profile ID and exact earned state. The schema marker changes in
  the same `BEGIN IMMEDIATE` transaction, so restart cannot duplicate it. An
  impossible/failed migration is retryable and never resets the legacy record.
- Public Player Name, Recovery Code, and backend device-session authentication
  are implemented in Batch 1. Profile rename/deletion, cloud sync, PvP,
  active-battle checkpoints, and migration between account systems remain
  deferred. Public Stage/Arena battle operations are implemented for isolated
  testing behind the default-off `BATTLE_API_ENABLE_PUBLIC_BATTLES` server
  gate; player-facing onboarding and Public launch remain pending later gates.

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
and completion receipts scoped by profile and battle session. Structured
campaign mode completion is stored separately per profile, campaign, battle,
and mode. Existing stage progress remains the sequential Learner authority;
Tactics availability is derived per campaign from completion of every
configured Learner battle. Arena Run adds an
optional profile-scoped immutable squad, twelve persisted nodes, and node
completion receipts. `BEGIN IMMEDIATE`
makes each slot initialization/overwrite, active selection, or victory
receipt/progress/reward change atomic.

New slots start with exactly Warrior Weapon Master, Mage Comprehensiveness,
Priest Comprehensiveness, and Rogue Comprehensiveness, zero stage progress, and
no rewards. Learner is available by default; Tactics is locked separately in
each campaign. Confirmed overwrite replaces only the named occupied slot with a
new stable profile identity and fresh state in one transaction. Cancelling or
withholding confirmation makes no write.

Arena Run creation validates exactly six distinct owned definition IDs and
atomically stores the ordered squad plus twelve server-seeded nodes. Only the
current node may launch; only its authoritative friendly victory can add a
receipt and advance the run. Duplicate completion returns existing state
without advancing twice. Loss and draw leave the node retryable. A completed
round-limit resolves to an ordinary authoritative victory or draw; only a
friendly victory may advance the node.
An explicitly confirmed abandon atomically deletes that active profile's run
and its twelve-node records; it does not alter its unlocks, training progress,
or other save slots. A new run remains an intentional six-hero squad action.
After an acknowledged twelfth victory, the browser returns to Stage Map. On a
later Arena visit, the persisted completed run opens the replacement squad
builder; the completed record is not removed until the replacement six-hero
squad is confirmed and accepted. This presentation flow does not change the
store's atomic run-replacement semantics.
Live battles remain process-local. Browser reload does not itself create or
resume a battle; it returns to preparation, and a later explicit Enter Battle
creates a fresh attempt from the still-persisted node configuration. The
Arena node's legacy stored battle seed remains readable but no longer fixes
retry combat randomness. Existing run and save-slot rows need no migration.

## Save and Checkpoint Behaviour

### Permanent Progression

Save persistent progression immediately after it successfully changes. Examples
include stage completion, hero unlocks, and other permanent progression
rewards. Learner victories retain the existing sequential stage and reward
path. An unlocked Tactics victory records that battle's own completion without
advancing Learner or granting a hero or item-card reward. A client-visible
success must not be reported before the authoritative
backend has committed the corresponding persistent change.

### Active PvE and Training Battles (Deferred)

UI-021 does not save active battles. At battle start, the backend creates an
in-memory battle session only; a refresh/restart cannot resume it and grants no
progress until a completion transaction succeeds. Structured sessions retain
the active profile identity from launch; completion after a slot switch is
rejected instead of leaking a result into the new active slot.


### Battle Completion

After an authoritative friendly structured-battle victory, the completion route
reads the immutable mode bound to the launched session. Learner records a
durable receipt, updates the stage, applies a permitted unlock or generic
item-card reward, and returns the updated profile in one transaction. Tactics
records only its mode-specific completion, idempotently and without rewards.
Defeat, draw, and resign do not complete either mode. A slot switch prevents
the old session from writing to the newly active profile. Receipts make
reload/retry/replay calls idempotent. Completion does not save or
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
- Migrate historical structured stage completions as Learner history without
  replaying reward grants. An already-completed campaign gains Tactics access;
  an incomplete one remains locked. Keep profile and slot isolation, including
  on overwrite and reload.
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

- 2026-10-27 — Added profile/campaign/battle/mode completion ownership,
  Learner-only rewards, per-campaign Tactics access, and legacy Learner migration.
- 2026-08-10 — Renamed from `Save_System.md`; documented agreed player-data,
  SQLite-direction, backend-authoritative autosave/recovery, completion, and
  abandonment principles. No persistence implementation was added.
- 2026-08-19 — Implemented the limited default-profile SQLite progression
  store for UI-020 training rewards; profiles, inventory, and battle recovery
  remain deferred.
- 2026-08-20 — Upgraded to schema version 2 with five isolated slots,
  backend-owned active selection, safe UI-020 migration, and confirmed
  transactional overwrite.
- 2026-08-31 — Upgraded to schema version 3 with per-profile Arena Run
  schedule/squad/node persistence and idempotent node advancement.


## Online Pre-Alpha Identity and Persistence Extension

The first small external online pre-alpha test will continue using the existing **SQLite** persistence model on a single backend VM. This is an extension of the implemented local persistence direction, not a declaration that SQLite is the final production online database.

The initial backend hosting direction is **Google Compute Engine e2-micro**, running the authoritative FastAPI + Python engine. Persistent SQLite data resides server-side with that backend deployment; React/browser clients never directly own or write authoritative progression.

Because server-side SQLite creates dependence on the VM's persistent disk, the online deployment must establish an appropriate database backup procedure. A later migration to PostgreSQL/Supabase remains expected when multi-instance deployment, stronger cloud recovery, larger-scale telemetry, mature online accounts, or serious PvP requirements justify it.

### Online Player Identity — RELEASE-002 Batch 1

The 12 September proposal of a unique name plus name-and-code recovery was
superseded by the approved RELEASE-002 policy. A Player ID is a permanent
server-generated UUID. Player Names are case-preserving, **not unique**, 3–20
ASCII letters, digits, or underscores; they are display-only, never a
credential. Recovery requires the code **alone**.

At enrollment the backend generates 16 independent characters from the exact
32-symbol alphabet `23456789ABCDEFGHJKLMNPQRSTUVWXYZ`, formatted in four
groups of four. The 80-bit code is disclosed only in the initial no-store
response. A keyed, domain-separated HMAC-SHA-256 verifier and key version are
stored; plaintext is not. The player must explicitly acknowledge saving the
code before ordinary Public save access. An authenticated Forgot Recovery Code
action immediately replaces the prior code and requires a fresh acknowledgment.
There is no ordinary regeneration, and losing both session and code has no
self-service recovery.

The backend issues one active device session per Player ID. A new-device
code-only recovery revokes the previous session and increments its generation.
Sessions have 30-day sliding expiry, bounded credential rotation and brief
same-device token overlap. The opaque session secret is in a host-only
`Secure; HttpOnly; SameSite=Lax` cookie; the database keeps only a verifier.
Unsafe Public requests require exact Origin and session-bound CSRF checks.
Recovery failures are counted in SQLite under a keyed IP digest: the tenth
failure within 15 minutes triggers a 15-minute block, without a permanent
account lock. Only a trusted configured proxy can supply the client-IP header.

Public schema v5 owns `players`, `player_sessions`, recovery-attempt/block
tables, five `(player_id, slot_id)` positions, and a player-specific active
slot. A saved profile and its unlocks, Stage progress, rewards, and Arena run
belong to its slot owner. Reads resolve that owner's active profile; writes
also revalidate the live session inside the same SQLite transaction. Public
initialization is explicit on a clean database outside the repository and
fails closed if the runtime database is missing or incompatible. Development
schema v4 and existing saves stay isolated and unchanged.

Batch 2 retains the Public v5 identity/save format and adds an explicit
`public_battle_schema_revision=2` marker for its expanded battle lease and
diagnostic foundation. A database initialized by the earlier Batch 1 shape
fails closed with an offline-upgrade requirement; runtime does not silently
alter, reinitialize, or discard it. Before any later Public launch, an
owner-approved offline migration must be rehearsed on a verified backup if
such a database contains data. This batch does not operate on a real save DB.

Batch 1 created the battle lease, diagnostic, and settlement schema foundations.
Batch 2 uses them for isolated Public Stage/Arena testing only. A normal Public
process still omits all battle routes unless the server explicitly enables the
Batch 2 test gate; even then generic and Debug creation are absent. The live
engine is still RAM-only: startup reconciles unfinished leases rather than
resuming battles. Diagnostics and original terminal receipts survive cleanup
and restart. A confirmed friendly Victory commits Stage/Arena progression and
the receipt before its response; a later completion call reads the receipt,
not a second grant. Resign or 30-minute inactivity before confirmed Victory
releases capacity without a reward. Batch 2 does not add onboarding, deploy
Public access, configure backups, or approve Public release. The older local/
Development completion flow above remains a Development compatibility path.

### Public client and backup integration — RELEASE-002 Batch 3

The Public client now presents Create New Player, code-only recovery, the
one-time Recovery Code and explicit backend acknowledgment, then that player's
five server-owned slots. An authenticated Forgot Recovery Code action replaces
the code and requires another acknowledgment. The frontend never persists the
code or session token in local/session storage; the host-only HttpOnly cookie
remains session authority, with an in-memory CSRF token. Direct protected-page
reload checks the current session read-only. Near-expiry refresh is a separate
protected POST. Authentication loss clears player-specific client views and
cross-tab notification carries no secret. A CSRF rejection revalidates without
replaying an unsafe action.

`battle_api.public_db_ops` supplies an operator-invoked online backup,
integrity/schema inspection, seven-daily and separate release retention, and
isolated no-overwrite restore validation. It also has a confirmation-gated,
backup-first offline upgrade for one exact modeled Batch 1 Public-v5
foundation shape. No actual legacy deployed DB has been inspected; a real
legacy upgrade remains blocked pending an authorized disposable fixture.
Systemd/GCS templates and local HTTPS tests do not establish deployment
readiness on GCE. Public battle access stays default-off until separate owner
launch authorization and all host/backup/capacity checks pass.

### Scope Boundary

This extension does **not** authorize or imply:

- email/password registration;
- email verification;
- Google/Apple/social login;
- a conventional account-management system;
- cloud synchronization independent of the authoritative backend;
- persistent live-battle checkpoints;
- Redis;
- multi-instance backend deployment;
- PvP reconnect/recovery.

Live battles remain process-local/in-memory under the existing design. A backend restart may terminate an active pre-alpha battle, while already committed permanent player progression remains in SQLite.

### Migration Principle

The online pre-alpha implementation should preserve the existing domain separation and stable identifiers so that SQLite can later be replaced by PostgreSQL/Supabase or another server database without redefining player identity, hero ownership, progression, Arena Run state, or battle/session concepts.

## Change Log Addition

- 2026-11-18 — Added Batch 3 client recovery/session integration and
  operator-only backup/restore boundary; live deployment remains unverified.
- 2026-11-17 — RELEASE-002 Batch 2 documents default-off isolated Public
  Stage/Arena battle leases, inactivity/Resign and durable terminal receipts;
  Public player access and live-battle resume remain closed/deferred.
- 2026-11-16 — RELEASE-002 Batch 1 adds the isolated Public schema-v5
  player/session/Recovery Code and per-player five-slot backend foundation.
  Corrected the superseded name-and-code/unique-name proposal; Public battles
  and onboarding remain gated for later batches.
- 2026-09-12 — Historical first online pre-alpha proposal: retain SQLite on
  the initial single Google e2-micro backend and add player identity/recovery.
  Its unique-name/name-plus-code details were superseded on 2026-11-16.
