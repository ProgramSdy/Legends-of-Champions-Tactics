# Python battle adapter and API

## Stage 5.3 local telemetry boundary

Public telemetry is **disabled by default**. It requires both backend
`BATTLE_API_ENABLE_PUBLIC_TELEMETRY=1` on an explicitly offline-migrated Public
schema-v5 database and frontend `NEXT_PUBLIC_TELEMETRY_ENABLED=true` in a newly
built client. These gates are not approved for the live Public service. The
Development API does not register this as a Development gameplay feature.

When enabled, `POST /api/v1/telemetry/events` accepts one strict schema-version-1
browser observation: UUID `eventId`, `visitorId`, `sessionId`; `eventType` of
`landing_view`, `home_view`, `session_activity`, or `client_error`; optional
timezone-aware `occurredAtUtc`; and type-specific bounded `eventData`.
`landing_view` carries an allowlisted `source` and optional campaign;
`session_activity` carries only an allowed activity label; `client_error`
carries only a stable code and route ID, never message, URL, stack or secrets.
The server owns receipt time, authenticated player linkage, environment and
build. A valid request receives HTTP 202 with `{contractVersion: "1.0",
accepted, duplicate, reason}`; duplicates and caps are explicit and never
affect gameplay. With the backend gate off, the route is unavailable (404).
Origin and existing session/CSRF protections apply where relevant.

Authoritative battle activation is captured separately after the canonical
commit; outcomes remain in existing battle diagnostics. The telemetry sidecar
does not change battle actions or rewards. Restricted CSV/SQL KPI/battle exports
and bounded raw retention are offline operator commands, not HTTP endpoints;
see [Pre-Alpha Telemetry Architecture](../Technical/Pre_Alpha_Telemetry_Architecture.md).

## Runtime

Install `requirements.txt` plus `requirements-api.txt`, then start the
development API from the repository root:

```bash
make dev
```

`make dev` starts the adapter on port 8001 and the web client on port 3001;
press Ctrl-C once to stop both. To run the adapter independently, use:

```bash
make backend
```

Both commands explicitly set `LOCT_RELEASE_MODE=development`, which registers
the Engineering Test route. Start the public-safe backend with:

```bash
make backend-public
```

That target explicitly sets `LOCT_RELEASE_MODE=public`, so
`POST /api/v1/debug/battles` is absent from routing and OpenAPI. A missing,
empty, or unrecognized `LOCT_RELEASE_MODE` also resolves to `public`; a bare
`uvicorn battle_api.app:app` therefore fails closed. Check the mode that a new
adapter process would use with:

```bash
LOCT_RELEASE_MODE=development .venv/bin/python -m battle_api.release_mode
LOCT_RELEASE_MODE=public .venv/bin/python -m battle_api.release_mode
```

### Same-Wi-Fi development access

For a temporary local-network playtest, run this from the repository root:

```bash
make lan
```

It detects the Mac Wi-Fi address from `en0`, binds the development frontend and
adapter to the LAN, configures the browser to use that same host for the API,
and restricts API CORS to that explicit browser origin plus the two local
origins. If Wi-Fi is on another interface, provide the address yourself:

```bash
make lan LAN_HOST=192.168.1.42
```

Open `http://<LAN_HOST>:3001` from another device on the same trusted network.
Allow incoming connections for ports 3001 and 8001 in macOS Firewall if asked.
This is an unauthenticated development mode, not an Internet-facing deployment:
do not use it on untrusted/shared networks or forward these ports through a
router.

If the LAN start screen opens **Enter the Valley** instead of **Local
Adventure**, or player entry reports HTTP 404 for
`/api/v1/sessions/current`, check for old frontend/backend processes still
listening on ports 3001 and 8001. A process started before the explicit
Development-mode startup change does not inherit later Makefile or npm-script
edits. The Public-safe frontend calls same-origin `/api/`, which direct Vinext
development on port 3001 does not proxy; a bare backend may also report
`publicStoreNotConfigured`. Stop the stale local pair, then start a fresh
`make lan LAN_HOST=<your-LAN-IP>` from the repository root and leave it
running. That target explicitly sets `LOCT_RELEASE_MODE=development` for both
processes and `NEXT_PUBLIC_BATTLE_API_URL=http://<LAN-IP>:8001` for the web
client. Verify `http://<LAN-IP>:8001/api/v1/health` returns 200 and that the
browser's player-entry request goes to port 8001. Restart **both** processes
after changing release mode or API origin; backend routes and frontend runtime
configuration are chosen at process startup. Do not point local Development
at the Public database or server to work around a local 404.

Development CORS allows exactly `http://localhost:3001` and
`http://127.0.0.1:3001` by default. Override the exact allowlist with a
comma-separated environment variable:

```bash
BATTLE_API_CORS_ORIGINS=http://localhost:3001,http://127.0.0.1:3001 \
  LOCT_RELEASE_MODE=development \
  uvicorn battle_api.app:app --reload --port 8001
```

Wildcard origins are ignored and credentials are disabled. Production origins
must therefore be explicitly configured.

The FastAPI handlers are async and perform no database or network I/O. They
offload synchronous legacy-engine work through `asyncio.to_thread`; resolution
is protected by per-session and module-global RNG locks, so it does not block
the ASGI event loop or interleave the engine's module-global random state.

## Endpoints

### `GET /api/v1/health`

Returns service and contract version health.

### `GET /api/v1/heroes`

Returns contract version `1.0` and exactly the ten approved hero definitions.
Each definition includes stable `definitionId`, display name, faculty, and
specialization, plus the read-only Hero Gallery fields: exactly four configured
starting-stat ranges (`id`, `label`, `minimum`, `maximum`), exactly seven
configured resistance ranges of the same shape, a stable skill inventory
(`skillId`, `displayName`, `isPassive`, `reference`), and `unlockSource`
(`starter`, a stage-reward descriptor, or `null`). `reference` is an additive
strictly typed skill-facts record: audited target semantics, skill type,
active/passive status, attack/damage classifications, and Base Damage/Base
Healing availability.
The optional nullable `cooldownRounds` reference reports the engine's
initial cooldown counter only for skills that assign one: Shadow Evasion `2`;
Shield Bash, Thunder Pot, Antivenom Potion, Warlust, Heroric Charge, and
Shield of Protection `3`. The other 26 published skills return `null`.
It is not the live `cooldownRemaining` snapshot field or buff duration.
Numerical results are either audited baseline-power
bounds, an explicit unavailable reason/note (optionally with an
adapter-authored display label and static calculation title/text for a Gallery
help dialog), or not applicable; classification
states distinguish missing applicable data (`unclassified`) from a genuinely
inapplicable concept. These fields are catalogue facts only:
they do not create heroes, roll randomized values, consume RNG, or grant an
unlock. The browser must render ranges as ranges, obtain actual ownership from
`GET /api/v1/progression`, and must not infer a missing unlock route.
An available numeric reference keeps a required string `note`; an empty string
means the Gallery shows only the audited range and no explanatory line.
Every reference also carries the additive `continuousDamage` numeric-reference
field. It is `notApplicable` unless an ongoing-damage value has been audited;
it uses the same discriminated numeric-reference shape as `baseDamage` and
`baseHealing`.

The adapter maps target presentation from its audited legal-target semantics,
not raw engine `target_type` alone. Reference metadata is static and never
executes a skill or opens a session; it is not a calculation of damage dealt
or healing received in a live battle. React renders any supplied calculation
copy verbatim and must not derive or duplicate formula logic.

The currently audited Target-dependent Gallery entries are Shadow Word Pain,
Sharp Blade, Poisoned Dagger, Fatal Strike, Armor Crush, Devastate, Shield
Bash, Thunder Pot, Moon Slash, Strike of Meteorite, Hammer of Anger, Hammer of
Revenge, and Heroric Charge. The five Warrior
Defence/Berserker entries use an empty card note and an adapter-authored
direct-damage formula in the existing calculation popup. Fatal Strike and
Armor Crush carry adapter-authored direct-damage formula copy and the
latter's 55%/65%/75% Armor Breaker multiplier bands; the calculation text is
not a final damage result or a status-outcome guarantee. Weapon Master's
Antivenom Potion instead publishes available Base Healing `18–20` as
self-healing power before modifiers and the HP cap, with damage fields not
applicable. These are static catalogue facts, not a new API shape or preview.
The three Paladin entries likewise publish direct-damage formula copy with no
card note: Hammer of Anger includes the active Wrath of Crusader bonus bands,
Hammer of Revenge names its self-debuff bonus without listing bands, and
Heroic Charge includes the engine's one-damage floor. Heroic Charge retains
the historical `skill.paladin.heroric_charge` ID but uses the corrected Gallery
display name. It publishes Base Healing 28–32 on hit, evasion, and prevention
paths alike. Holy Aura publishes 6–8 Base Healing per living
recipient at round start. Crusader Strike and
Shield of Righteous each publish fixed direct power 18–22; Holy Blast publishes
20–25 for its first target and 14–17 for the second. Priest Discipline's
Penance publishes enemy damage power 17–21 and ally healing power 21–25;
Flash of Light publishes unbuffed Base Healing 19–21 and Purify Healing
publishes Base Healing 23–27. These static power ranges do not include live
Wrath stacks, target healing modifiers, or the recipient's remaining HP;
those remain battle-preview/engine concerns.
Holy Word Punishment publishes immediate damage power 7–11, excluding its
periodic effect. Holy Word Punishment separately publishes Continuous Damage
9–16 per activation. Its Gallery box contains only that range, with no note or
branch conditions, because both new and recycled debuffs use the same
`ceil(1.3 × direct roll)` stored effect and later ±1 tick variation. An
already-active debuff is not refreshed. The three later round-start
activations remain engine-owned; the catalogue does not publish a lifetime
total. None of these are final receipt/HP
predictions.
The roster display name is catalogue metadata. Each non-summoned battle
combatant receives a runtime name from its class's `HeroGenerator` faculty pool
during session creation.

Warrior Berserker publishes Blood Frenzy as a fourth `isPassive` inventory
item. Its runtime `Skill` is a non-interactive marker; the existing
`Hero.take_damage` → `trigger_blood_frenzy` path alone decides activation.
The Gallery receives a static self/effect reference with damage and healing
numbers not applicable. Battle snapshots may display the passive, but the
adapter excludes it from legal commands and battle previews.

Priest Discipline's Holy Concentration is a fourth `isPassive` Gallery
inventory item with a static self/effect reference and inapplicable numeric
facts. It documents the existing low-HP Holy Word Redemption extra-recipient
branch in `Skill.execute`; there is no corresponding selectable runtime Skill,
and battle commands and mechanics are unchanged.

Paladin Retribution's `skill.paladin.wrath_of_crusader` is also a fourth,
catalogue-only `isPassive` entry. Its self/effect reference has inapplicable
damage/healing/classification fields because the existing Crusader Strike buff
supplies Hammer of Anger and Flash of Light bonuses through their live skills.
It is not a separate runtime `Skill`, legal command, or new mechanic.

The current roster includes Priest Comprehensiveness and Discipline; Paladin
Retribution, Protection, and Holy; Mage Comprehensiveness; Warrior Defence,
Weapon Master, and Berserker; and Rogue Comprehensiveness. `displayName`
remains a required non-empty transport field even when a presentation surface
chooses to show only faculty and specialization.

The catalogue stays static so that a locked definition can still be validated
and rendered as a fixed training-stage enemy. Active-slot ownership is returned
separately by `GET /api/v1/progression` and enforced for every friendly team.

### Five-slot save APIs

RELEASE-002 Batch 1 preserves these anonymous contracts in **Development**.
In **Public**, the same paths are scoped to the authenticated Player ID and
the player's five independent slots. The active slot is per player, never a
global singleton. A confirmed Public session is required for save listing,
create/load/confirmed overwrite, progression, Stage listing, and Arena
progression reads/writes. Unsafe requests additionally require exact Origin
and a session-bound CSRF token; no request body may supply Player ID or profile
authority. Public writes recheck session generation, expiry, acknowledgment,
and owned slot/profile inside their SQLite transaction. A missing or revoked
session returns typed 401; an unacknowledged code returns typed 403. Normal
Development callers and schema-v4 saves are unchanged.

Public Batch 1 identity endpoints are:

| Method and path | Request | Result |
| --- | --- | --- |
| `POST /api/v1/players` | `{ "playerName": "..." }` | Player ID/name, expiry, confirmation state, CSRF token, and one-time Recovery Code; session cookies. |
| `POST /api/v1/sessions/recover` | `{ "recoveryCode": "XXXX-XXXX-XXXX-XXXX" }` | Same Player ID/name with a new session; prior device revoked. No code redisclosure. |
| `GET /api/v1/sessions/current` | none | Current Player ID/name, expiry, confirmation state, CSRF token; never redisplays the code. |
| `POST /api/v1/sessions/refresh` | empty object | Origin/CSRF-protected session renewal and bounded credential rotation; read-only GET does not extend expiry. |
| `POST /api/v1/recovery-code/acknowledge` | empty object | Marks the issued code saved, enabling Public save access. |
| `POST /api/v1/recovery-code/forgot` | empty object | Immediately replaces the old code; one-time replacement code response and renewed acknowledgment requirement. |
| `POST /api/v1/sessions/logout` | empty object | Revokes the session and clears cookies; no content. |

Player Names are case-preserving, non-unique, 3–20 ASCII
`[A-Za-z0-9_]`, and not credentials. The Recovery Code is 16 independent
unambiguous base-32 characters, formatted in four groups; the server stores
only a keyed verifier. Enrollment/replacement responses and session cookies
are `Cache-Control: no-store`. The authentication cookie is host-only,
`Secure; HttpOnly; SameSite=Lax`; the CSRF token is not the authentication
secret. Recovery is limited to ten failures per canonical client IP in a
15-minute rolling window followed by a 15-minute temporary block. Public
runtime requires an explicitly initialized, compatible, separately configured
database and protected keys; missing configuration fails closed.

**RELEASE-002 Batch 2 isolated Public battle contract.** A default Public
process continues to omit all battle paths and OpenAPI entries. Only an
isolated process with exact server-side `BATTLE_API_ENABLE_PUBLIC_BATTLES=1`
registers authenticated Stage/Arena launch, shared state/command/preview,
`POST /api/v1/battles/{battleId}/resign`, and Stage/Arena completion receipt
paths. Generic `POST /api/v1/battles` and Engineering Debug creation remain
unregistered in Public, even with this opt-in. This is backend test access,
not Public-player release approval. Static hero/manual catalogues remain
read-only and anonymous.

Public battle IDs are lookup identifiers, not credentials. Every protected
battle route requires the confirmed Player session; unsafe routes also require
exact Origin and CSRF. The server binds Player ID, launch slot/profile,
session generation, Stage/Arena context, and lifecycle at creation. A foreign
battle is hidden; revoked or stale launch context cannot continue gameplay or
redirect a reward. The server reserves a provisional SQLite lease before RAM
construction, enforces one active battle per Player ID and an initial global
cap of 20, then activates the same battle ID. The two-minute provisional TTL
and 30-minute active inactivity deadline are server-owned. Only completion of
a newly accepted player command and its automatic follow-up refreshes the
active deadline; GET, preview, rejected/duplicate command, AI alone and UI
playback do not. Additive response fields are `serverNow`, `expiresAt`,
`lifecycleStatus`, optional `terminalReason`, and `settlementStatus`; later
frontend warnings derive time from these values, not a local authority.

Public Stage launch rejects a request containing `seed`, including explicit
`null`; Arena has no caller seed. Each new attempt receives a server-generated
effective 256-bit combat seed recorded as canonical hex in server-only
diagnostics and never echoed to clients. Development generic/Stage/Debug
explicit seeds remain unchanged. Terminal Stage/Arena Victory is settled
atomically before its confirmed command response: one transaction writes the
outcome, existing progression/reward effect, original receipt and lease
release. Defeat/Draw grant none. A later completion call is an idempotent
receipt read, not another reward path. Resign is owner-authenticated and
idempotent; before a confirmed Victory it abandons without reward, while a
settled Victory retains its original result. Storage failure leaves no
confirmed Victory and a retryable pending state while the RAM session lives.
There is no battle resume or full replay after process restart.

**RELEASE-002 Batch 3 frontend consumption.** This batch does not change the
`1.0` request/response schema or combat formulas. In Public, the browser calls
the listed identity/save and Stage/Arena/battle routes on the same HTTPS
origin with cookies; unsafe requests carry the in-memory `X-CSRF-Token` from
the current session response. The HttpOnly session cookie is never read by
JavaScript. `GET /api/v1/sessions/current` and battle GET/preview remain
read-only; a near-expiry renewal uses only the explicit protected refresh
POST. A CSRF rejection is revalidated read-only and the unsafe request is not
automatically replayed. An uncertain battle command retains its original
`commandId` for retry; terminal completion displays the original durable
receipt. Resign Yes waits for the authenticated Resign response; No sends
nothing. `serverNow`/`expiresAt` drive one-time five- and one-minute UI
warnings but do not themselves renew a lease. Public player-facing Manual
formation data also uses same-origin transport; Development keeps its local
adapter URL and anonymous five-slot path.

`GET /api/v1/save-slots` returns `contractVersion`, nullable `activeSlotId`,
and exactly five ordered summaries. Each summary contains `slotId`, `occupied`,
nullable opaque `profileId`, nullable ISO-8601 `createdAt`/`lastPlayedAt`, and
`active`. Empty slots have null profile/timestamps and cannot be active.

- `POST /api/v1/save-slots/{slotId}/create` accepts no progression fields,
  initializes an empty slot with the exact four-hero starter state, and selects it.
- `POST /api/v1/save-slots/{slotId}/load` selects an occupied slot without
  resetting it and updates its last-played timestamp.
- `POST /api/v1/save-slots/{slotId}/overwrite` requires
  `{ "confirmOverwrite": true }`; it atomically replaces only that occupied
  slot with a new profile identity and fresh starter state.

All actions return `contractVersion`, `activeSlotId`, the selected `slot`, and
authoritative `progression`. Invalid IDs return 422 `invalidSaveSlot`;
occupied create, empty load, missing overwrite confirmation, missing active
selection, and a slot switch during a live structured battle return typed 409
errors. Store and migration failures return retryable 503
`progressionStoreUnavailable`. Clients must not send unlock, stage, reward, or
profile data.

### `GET /api/v1/progression`

Returns the active slot's opaque stable `profileId`,
`unlockedHeroDefinitionIds`, per-stage values (`highestCompletedBattle`,
`unlockedBattle`, `completed`, and campaign-specific mode availability and
one-based completed battle indices), and granted reward IDs/counts. Fresh slots own
exactly Warrior Weapon Master, Mage Comprehensiveness, Priest
Comprehensiveness, and Rogue Comprehensiveness. With no active slot it returns
409 `noActiveSaveSlot`. A schema-v1 default profile migrates once into active
slot 1 without changing its ID or earned state; corrupt, unsupported,
unreadable, incomplete, or failed migration state returns retryable 503 rather
than resetting or selecting another slot.

### `GET /api/v1/stages`

Returns the two authoritative nine-battle curricula, including each fixed
enemy definition order, battle size, formation, optional reward metadata, and
server-computed `unlocked`/`completed` Learner flags. Each stage also exposes
`modes.learner` and `modes.tactics`, each with `available`, `completed`, and
`completedBattleIndices` (one-based display orders). Tactics unlocks per
campaign only when all configured Learner battles are complete; its completion
is independent and nonsequential. The UI may compare this to its presentation
config, but must not calculate access or rewards itself.

### `POST /api/v1/stages/{stageId}/battles/{battleIndex}`

Creates one accessible structured battle. Its body contains the player team,
a player-selected formation when the size is 2v2/3v3, an optional deliberately
supplied reproducibility `seed`, and optional opaque `attemptId`. It accepts
`mode: "learner" | "tactics"` with Learner as the default when omitted by a
legacy structured-stage caller. The normal player UI supplies explicit mode
and `attemptId`, omitting `seed`; an unknown mode fails typed validation, and
locked Tactics returns a stage access conflict. A new intentional launch gets
fresh server-owned entropy. The route owns the exact size, fixed computer enemy definition order,
and fixed enemy formation; locked player definitions are rejected but locked
static enemies are allowed. The player formation uses the same size-specific
choices as Arena and must be omitted for 1v1. A locked step returns HTTP 409;
an unknown `stageId` or an out-of-range battle index is rejected by the typed
route with HTTP 422. An in-range locked or unavailable step returns HTTP 409.
The normal Arena `POST /api/v1/battles` creation contract is
unchanged, except it also rejects a locked friendly definition with HTTP 409
`heroLocked`.

`POST /api/v1/arena/runs/{runId}/nodes/{nodeIndex}/battles` also accepts an
optional `attemptId` alongside its ordered player team and size-valid player
formation. The persisted Arena node retains its schedule, enemy definitions,
and enemy formation, but its legacy stored battle seed does not drive new
attempts. For either player-facing creation route, the same `attemptId` and
identical active profile/route/configuration replays the original battle
envelope in the same process without drawing another seed. A changed profile,
route, structured mode, or configuration under the same ID returns HTTP 409
`battleAttemptConflict`. Without `attemptId`, each valid POST is a separate
launch for compatibility. A duplicate ID can replay its original session
even if another tab has since advanced or abandoned the Arena run; such an
obsolete session cannot commit progression. The binding is process-local and
does not provide reload recovery or cross-restart/cross-worker exactly-once
creation. Explicit equal stage seeds remain reproducible for developer/API
tests; free-form debug creation is unchanged.

### `POST /api/v1/battles/{battleId}/completion`

Commits a structured session only after its authoritative snapshot has ended in
a friendly victory. For Learner, one SQLite transaction records the battle
receipt, advances sequential stage progress, and applies its unlock/item-card
reward. For Tactics, it records only that campaign/battle's Tactics completion,
without Learner progress or rewards. Completion reads the immutable session
mode, never a client-supplied completion mode. The response includes
`alreadyCommitted`, `newlyGrantedRewards`, and refreshed progression. Replays,
retries, and duplicate callbacks return the committed state without granting
again. Completion is bound to the profile active when the structured session
launched; a later slot switch returns 409 `activeSaveSlotChanged`. Arena or
non-victory sessions return a structured rejection.

### `POST /api/v1/arena/runs/{runId}/abandon`

Requires no client-supplied profile, squad, node, or outcome data. The adapter
looks up the active save slot, deletes only that slot's matching Arena Run, and
returns the ordinary Arena-state envelope with `run: null`. An unknown,
completed-for-another-slot, or non-matching run ID returns the structured
`arenaRunNotFound` error. The UI exposes this endpoint only after the player
chooses YES in the Give Up Current Run confirmation.

### `POST /api/v1/battles`

Request:

```json
{
  "battleSize": 2,
  "playerTeam": [
    "hero.warrior.weapon_master",
    "hero.warrior.defence"
  ],
  "playerFormation": "front-rear",
  "enemyCompositionMode": "specified",
  "enemyTeam": [
    "hero.rogue.comprehensiveness",
    "hero.priest.comprehensiveness"
  ],
  "enemyControlMode": "player",
  "enemyFormation": "side-by-side",
  "seed": 42
}
```

`battleSize` is 1, 2, or 3. Player and specified-enemy arrays must match that
size and contain only roster IDs. `enemyTeam` is omitted in random mode.
Repeated definitions and cross-team overlap are allowed. `seed` is optional.
The legacy `{"scenarioId":"ragnar-vs-nighthawk"}` request remains accepted.

For `battleSize: 2`, `playerFormation` is required and is exactly
`front-rear` or `side-by-side`. `enemyFormation` is required for a
player-controlled enemy. It may be omitted for a computer-controlled enemy;
the adapter then chooses one permitted value from the session-seeded random
stream.

For `battleSize: 3`, `playerFormation` is required and is exactly
`one-front-two-rear`, `two-front-one-rear`, or `all-front`. A
player-controlled enemy requires `enemyFormation` from the same three-value
set. A computer-controlled enemy must omit `enemyFormation`; the adapter
chooses one of those three values using the session-seeded random stream.
Wrong-size formation IDs are rejected rather than coerced. Formation fields
remain prohibited for 1v1. The adapter maps each size-specific formation and
ordered team to engine constructor positions and serializes the actual
formations plus each combatant's `front`/`rear` position.

Random composition is selected inside the adapter with session-seeded
randomness. The response is a v1 envelope containing ordered initial and
computer-turn events plus the snapshot at the next player turn or battle end.
For an automatically resolved opening, it also additively includes
`openingSnapshot` (the authoritative state before automatic opening events are
presented) and `playOpening: true`. The client begins its visible queue from
that snapshot, plays the returned events in order, then reconciles to the
returned final snapshot and revision. Player-first openings retain
`playOpening: false`; their ordinary initial snapshot remains immediately
usable after the entry overlay.

Every serialized combatant now includes additive `stats`: Damage, Defence,
Agility, and Fire/Frost/Arcane/Shadow/Death/Poison/Nature resistance entries,
each with finite `current` and signed `delta` numbers. A frozen per-instance
Hero baseline is captured after property generation/resistance compensation,
before opening effects; summoned heroes capture their own baseline at
construction. Python alone subtracts baseline from current values and
normalizes exact zero without rounding nonzero fractions. Snapshot inspection
does not mutate a hero/session, consume RNG, issue a command, or advance a
revision. The battle envelope remains an untyped dictionary at the HTTP/OpenAPI
level, so its published OpenAPI schema is unchanged; existing clients can
ignore the additional combatant field. See `BATTLE_DATA_CONTRACT_V1.md` for
the exact nested shape and presentation-timing rule.

### `GET /api/v1/battles/{battleId}`

Returns the current authoritative snapshot. Unknown IDs return HTTP 404 with a
structured `battleNotFound` detail.

### `POST /api/v1/battles/{battleId}/commands`

Request:

```json
{
  "type": "useSkill",
  "commandId": "cmd.browser.1",
  "expectedRevision": 0,
  "actorId": "enemy.nighthawk",
  "skillId": "skill.rogue.sharp_blade",
  "targetIds": ["friendly.ragnar"]
}
```

Rule-level rejections return HTTP 200 with `accepted: false`, a stable rejection
code, and the current snapshot. This lets the client reconcile stale state.
Malformed JSON is HTTP 422 and missing battles are HTTP 404. Duplicate command
IDs return the originally stored result without resolving the engine again.

When the next actor is computer-controlled, the adapter continues resolving
existing engine AI turns before returning. The accepted response includes all
ordered events, its final revision, and the snapshot at the next player turn or
battle end.

Responses may add `battleLog` events carrying sanitized Python-authored
presentation lines. `channel` is `battleInfo` or `statusUpdate`. Typed semantic
events remain authoritative for mutations and playback; `visibleInLog: false`
only suppresses their generic text when a Python line would duplicate it.

Round-start status processing is an ordered engine journal: the adapter emits
one typed HP event for every `take_healing` or `take_damage` activation reached
from `StatusEffectManager.check_heroes_status_effects`, with its intermediate
`hpAfter`, `statusId`, and known source. It never substitutes a single net HP
event for several status activations on one hero. Holy Aura is the first status
activation for each eligible recipient, followed by that method's existing
source order. The browser must play these events by `sequence`.

Each `statusApplied` event also includes the additive `statusPresentation`
classification: `buff`, `debuff`, or the compatible `neutral` fallback. The
adapter derives it from authoritative serialized status metadata; control
statuses use the harmful `debuff` presentation. Existing `effectHint: "status"`,
status duration, source and target fields remain unchanged.

`statusApplied` also carries the additive nullable `stacks` field whenever the
serialized post-event status has a stack count. The adapter emits it for a new
status and for a retained status whose stack count, source, kind, or refreshed
duration changes. A duration-only countdown tick does not create a synthetic
status-application event. This changes neither status rules nor the v1 event
ordering; older consumers can ignore the optional field.

`damagePrevented` is an additive typed semantic event for an incoming action
that the engine explicitly prevented through Shield of Protection. It includes
stable `sourceId`, `targetId`, `skillId`, `amount: 0`, and
`reasonId: "status.shield_of_protection"`. The adapter emits it exactly once
per protected target from the engine's per-target immunity outcome/reason; it
does not infer prevention from unchanged HP. Evades, ordinary landed
zero-damage hits, Glacier, and Anti Magic Shield do not produce this event.
The event does not mutate HP or status state.

Every snapshot includes additive v1 `turnControl`. Its disposition is
`playerCommand`, `automaticAction`, `skip`, or `ended`; commands are accepted
only when `acceptsCommands` is true at a `playerCommand` boundary and the
submitted action matches the published `legalActions`. Automatic and skipped
states are classified by the engine-owned `Hero.turn_directive()` seam rather
than by adapter-local status rules.

For approved damage skills carrying an `attack_type`, legal actions also enforce
formation targeting. This includes the classified Warrior/Mage skills and the
owner-approved Paladin/Priest skills: Hammer of Anger and Holy Blast
(`ranged_projectile`); Crusader Strike and Shield of Righteous (`melee`); and
Hammer of Revenge, Heroric Charge, Holy Smite, Shadow Word Pain, Penance's
opponent branch, and Holy Word Punishment (`ranged_instant`). Melee excludes rear defenders while any
front defender lives; forced and computer actions consume this same target
list. Position damage adjustment remains inside `Hero.take_damage_calculation`
and is never calculated by the adapter or frontend.

Freeze, stun, paralysis, and fear are authoritative automatic skip states.
Affected player or computer actors expose no legal actions; the adapter emits
turn progression events and advances to the next actionable actor.

Scoff is resolved automatically from the engine directive's forced skill and
targets against its living initiator, regardless of the configured control
mode. Normal client actions are not exposed during that forced resolution. A
stale Scoff whose initiator is defeated is removed without consuming the turn.
The initiator is serialized as the status and turn-control source where
applicable.

## Source and rule mapping

## Stage 5.1 player-team and Development Debug authority

Stage 5.1 Development Debug adds `POST /api/v1/debug/battles/{battleId}/auto-actions`
with `{ "expectedRevision": number }`. It resolves at most one friendly player
turn through the existing specialization AI and normal adapter legality path,
then returns the ordinary battle envelope and ordered events. Stale revisions
are rejected; the server does not store an Auto Battle toggle. The route is
registered only when `LOCT_RELEASE_MODE=development`, so Public direct requests
and OpenAPI do not expose it. This operation is separate from battle preview,
which remains read-only and does not consume RNG or perform an action.

For every player-authored team launch (Development generic/Debug, Stage, Arena),
the adapter/API reject repeated stable Hero Profession definition IDs on the
player side with HTTP 422 detail code `duplicatePlayerProfession`. Distinct
specializations within a faculty and enemy-side repetition remain legal.

## BATTLE-TRANSPARENCY additive preview operation

`POST /api/v1/battles/{battleId}/preview` is an additive, revision-bound
information operation for the audited allowlist only: Mage Comprehensiveness
Fireball, Arcane Missiles, and Frost Bolt; Rogue Comprehensiveness Sharp Blade
and Poisoned Dagger; Priest Comprehensiveness Holy Smite, Shadow Word Pain,
and Binding Heal; Paladin Retribution Hammer of Anger, Crusader Strike, and
Flash of Light; Paladin Protection Hammer of Revenge, Shield of Righteous, and
Heroric Charge; Paladin Holy Purify Healing, Holy Blast, and Shield of
Protection; Priest Discipline Penance, Holy Word Redemption, and Holy Word
Punishment; Warrior Defence Devastate, Shield Bash, and Thunder Pot;
Warrior Weapon Master Fatal Strike, Armor Crush, and Antivenom Potion; and
Warrior Berserker Moon Slash, Warlust, and Strike of Meteorite. It accepts
`expectedRevision`, `actorId`, `skillId`, and `targetIds` and validates the
active actor, available skill, exact legal IDs/cardinality, and duplicate IDs
under the battle session lock. It does not execute a skill, enqueue events,
advance a turn or revision, mutate battle state, or consume the session/global
RNG.

Holy Aura remains passive-only and is not previewable. Paladin's additional
facts are produced by audited pure helpers: Revenge's live debuff-count bonus,
Righteous's on-hit reduction and actor defence state, Charge's live
control-immunity state, Purify's exact eligible removal ID set (never a chosen
random status), and Shield of Protection's actor damage-immunity state.
Unprovable Purify states and contradictory Charge Warlust/immunity state return
the ordinary unavailable coverage rather than approximating an action.

Each target response supplies current/max HP and an immediate `damage`,
`healing`, deterministic `prevented`, or status-only `null` primary. Only Holy
Word Redemption uses the status-only shape; it has no fabricated zero
damage/healing or Hit Chance. Direct damage/prevention
retains the evasion-only Hit Chance; healing uses a null Hit Chance and shows
post-modifier skill power before the live maximum-HP cap. Typed
material consequences can report a newly applicable Shadow Word Pain,
Binding Heal's separate post-modifier Priest heal (intentionally omitted from
the popup), Hammer's effective immediate Wrath damage contribution, Flash of
Light's stack-specific pre-receipt Wrath healing-power contribution, or Crusader
Strike's current live Wrath application, increase, or refresh. There is no DoT
or chain total, full-roster fallback, hidden formula input, or combined
hit/proc percentage. Arcane, Holy Blast, Moon Slash, and Thunder Pot accept a one-target
draft preview or their complete distinct legal pair, returning per-target facts
only; there is no aggregate total. Antivenom Potion and Warlust require an
empty target list and return typed `selfPreview` facts, rather than a fabricated
target. Shield of Protection uses the same targetless shape. This preview-only subset rule never changes the target count required
by `useSkill`.

Discipline Penance is side-aware only in the adapter: an ally gets Healing with
no Hit Chance, while an opponent gets direct Damage/Hit Chance and any
same-caster Redemption-linked recipient rows only `onHit`. Punishment uses the
published target cardinality: one target is a draft when two are published and
a complete command only when one is published (1v1/sole survivor). It reports
per-target direct facts and finite application/already-active status rows, not
an aggregate or future tick total. Low-HP Redemption extra-recipient and
foreign/global-record states return unavailable rather than predict RNG or a
false refresh.

For opponent Penance, `onHit` additionally requires valid direct selected-target
HP loss after the engine's authoritative damage receipt. Shield of Protection
and a fully absorbing Holy Word Shell therefore show no linked Redemption row;
a positive partial/ordinary receipt may show the row. A receipt range that can
both fully absorb and partially damage a linked-healing Penance target is
returned as the ordinary revision-bound unavailable preview rather than an
invented conditional range.

Warrior preview consequences remain discriminated API data. Armor Breaker
exposes first/next-stack/refresh plus resulting stacks; Stun exposes
application/extension; Scoff exposes application/refresh/source replacement;
Fatal Strike distinguishes application from already active; and the self-preview
union carries only material Antivenom/Warlust/Paladin self effects such as healing, supported
removal, resistance, control immunity, damage increase, and cooldown. React
must render those facts without recreating mechanics.

The evaluator uses audited pure range/receipt helpers under the existing
session lock. It never calls a mutable skill callback, mutates a battle clone,
or consumes session/global RNG. Existing Mage/Rogue response shapes remain
compatible; the only OpenAPI additions are the `healing` primary enum, nullable
healing Hit Chance, and discriminated material-consequence variants.

| Contract definition | Exact Python source | Constructor / engine skills |
|---|---|---|
| `hero.priest.comprehensiveness` / Aurelia | `heroes.priest.Priest_Comprehensiveness` | Holy Smite, Shadow Word Pain, Binding Heal |
| `hero.priest.discipline` / Seraphine | `heroes.priest.Priest_Discipline` | existing specialization skills and AI |
| `hero.paladin.retribution` / Valerius | `heroes.paladin.Paladin_Retribution` | existing specialization skills and AI |
| `hero.paladin.protection` / Bastion | `heroes.paladin.Paladin_Protection` | existing specialization skills and AI |
| `hero.mage.comprehensiveness` / Lyra | `heroes.mage.Mage_Comprehensiveness` | existing specialization skills and AI |
| `hero.warrior.defence` / Aegis | `heroes.warrior.Warrior_Defence` | existing specialization skills and AI |
| `hero.warrior.weapon_master` / Ragnar catalogue entry | `heroes.warrior.Warrior_Weapon_Master` | runtime Warrior-pool name; Fatal Strike, Armor Crush, Antivenom Potion |
| `hero.rogue.comprehensiveness` / Nighthawk catalogue entry | `heroes.rogue.Rogue_Comprehensiveness` | runtime Rogue-pool name; Sharp Blade, Poisoned Dagger, Shadow Evasion |
| Battle state and rounds | `game.game.Game` | `Game([ragnar], [nighthawk], "simulation")`, `game_initialization`, `start_round`, `end_round` |
| Target/evasion dispatch | `skills.skill.Skill` | `Skill.execute` and `Skill.resolve_targets` |
| Damage/defeat | `heroes.hero.Hero` | `take_damage`, `take_damage_action`, `check_if_defeated` |
| Round status/cooldown | `game.status_effect_manager.StatusEffectManager`, `Game.update_battle_information` | invoked by `Game.start_round`; per-activation HP journal preserves status execution order |

Target rules come from `Skill.target_qty`, `target_type`, `skill_type`, and the
engine-maintained living allies/opponents lists. Fatal Strike, Armor Crush,
Sharp Blade, and Poisoned Dagger require one living enemy. Antivenom Potion and
Shadow Evasion are targetless self buffs. There is no mana/resource system.

Fatal Strike applies healing reduction. Armor Crush applies/extends armor break
and can add bleeding/wound effects. Antivenom Potion heals, boosts poison
resistance, dispels supported bleeding/toxic effects, and starts a three-round
engine cooldown. Sharp Blade can apply bleeding. Poisoned Dagger can apply and
stack poison. Shadow Evasion grants temporary evasion and starts a two-round
engine cooldown. Other listed skills have no generic cooldown in their class
implementations.

## Known limitations and defects

- Hero construction depends on the two Excel workbooks under `data/`. The
  adapter uses a headless loader and intentionally avoids Pygame/image setup.
- The engine uses module-global `random`. Sessions retain independent RNG state
  and a module-global lock prevents cross-session interleaving. This is safe for
  the current process, but an engine-owned RNG dependency would scale better.
- Runtime names are selected from `HeroGenerator.hero_classes` inside that
  session random boundary. Same-faculty names are unique across both teams until
  the pool is exhausted, after which creation permits repeats. Name selection
  derives from then restores the session stream before hero construction;
  equal seeds/configurations remain reproducible without shifting established
  combat/stat rolls.
- The legacy `Skill.execute` API represents targetless buffs with the sentinel
  `["none"]` and has different scalar/list target shapes; the adapter contains
  narrow compatibility mappings.
- Event capture covers the approved heroes' explicit status registry. Expanding
  the whitelist requires synchronized engine lifecycle verification, stable
  adapter status/source/event mappings, matching frontend status metadata and
  effects, and cross-boundary regression tests; arbitrary Python attributes are
  never exposed.
- The process-local registry has no battle-state persistence or multi-worker
  consistency. Run one API worker. Public identity/expiry/quota and durable
  receipts are separate backend authorities; they do not make an unfinished
  RAM battle resumable after restart. Development remains anonymous.
- Rejections do not mutate engine state. Unexpected exceptions are not yet
  converted to a public adapter-error response; FastAPI returns its normal 500.
