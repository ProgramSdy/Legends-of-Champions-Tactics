# Technical Architecture

## Structured Computer Battle Strategies

## Battle Information Transparency

Battle previews are engine-owned, non-mutating audited facts transported by the
adapter at a specific revision. The UI requests and renders them only for the
approved Mage/Rogue damage skills plus Priest Comprehensiveness Holy Smite,
Shadow Word Pain, Binding Heal; Paladin Retribution Hammer of Anger, Crusader
Strike, Flash of Light; Paladin Protection Hammer of Revenge, Shield of
Righteous, Heroric Charge; Paladin Holy Purify Healing, Holy Blast, Shield of
Protection; Priest Discipline Penance, Holy Word Redemption, Holy Word
Punishment; and the finite nine-skill published Warrior roster. Holy Aura is a
passive and is intentionally outside the preview allowlist.
It is not a generic preview system. The
adapter returns typed immediate `damage`, `healing`, `prevented`, or finite
status-only `null` primary
facts and typed material consequences; React renders those facts and neither
runs skill callbacks nor copies combat formulas, caps, Wrath state, status
eligibility, target legality, or Warrior stack/refresh/control state.
Targetless Antivenom Potion, Warlust, and Shield of Protection use the same
session-locked contract with an empty target array and a typed `selfPreview`;
the UI does not invent a target. Paladin status/reduction/removal facts and
the post-evasion Holy Blast range are supplied as typed engine facts, not
recomputed in React.

Healing preview ranges deliberately communicate post-modifier skill power,
including for a full-health target. The live engine alone caps applied HP at
the recipient maximum.

Opponent Penance's same-caster Holy Word Redemption healing is an engine
mechanic gated by positive HP loss of the selected target after authoritative
receipt, rather than by raw attempted damage. A Shield of Protection or fully
absorbing Holy Word Shell receipt produces no linked healing; a partial or
ordinary positive receipt may do so. The adapter mirrors only definite finite
states and returns unavailable for a linked-healing receipt range that crosses
between zero and positive damage, rather than simulate combat or invent a
conditional formula in the client.

Preview evaluation uses audited pure range/receipt primitives under the current
revision/session lock. It cannot consume RNG, mutate heroes/session/events/
turns, call `Skill.execute`, or predict a seeded roll. Unsupported skills and
unprovable outcomes remain unavailable rather than approximated. The existing
Mage/Rogue contract stays compatible while healing introduces a null direct Hit
Chance and the expanded scope adds discriminated status, secondary-recipient,
and Wrath facts, including Flash of Light's typed stack-specific healing bonus.

New specialization-owned computer strategies follow the authoritative
study-first Part A / Part B / Part C standard in
`docs/Technical/Battle_Strategy_Template.md`. That template preserves the
engine/adapter legality boundary and requires real computer-turn regression
coverage; it does not change the shared `Hero` AI framework.

## Purpose

Authoritative high-level technical architecture for **Legends of Champions Tactics**.

## Current Sources

`onboarding/ENGINE_ARCHITECTURE.md` contains the foundation analysis. Current
HTTP/snapshot details are authoritative in `web-ui/PYTHON_ADAPTER_API.md` and
`web-ui/BATTLE_DATA_CONTRACT_V1.md`; gameplay rules are in `GDD/`.

## System Overview

The web product is a Next.js presentation client (`web-ui/`) connected over
HTTP to a thin FastAPI battle adapter. The adapter constructs and advances the
existing Python `Game`, `Hero`, and `Skill` objects. Python is the sole owner
of combat state, legality, randomness, AI, damage, and outcomes. The browser
submits intent and renders authoritative snapshots/events; it does not simulate
combat.

### First public HTTPS deployment (19 November 2026)

The owner-reported `RELEASE-003-db7f3395` deployment runs on a GCE
`us-central1-a` e2-micro VM. Browser HTTPS to
`loc-tactics.duckdns.org:443` enters Nginx, which proxies `/api/*` to the
single FastAPI/Uvicorn service on `127.0.0.1:8001` and other paths to Vinext
on `127.0.0.1:3001`; both application services are systemd-managed and
loopback-only. Public SQLite lives outside the release tree at
`/var/lib/loct/public/player.sqlite3`. The Owner first verified external HTTPS
API health and browser rendering, then separately authorized Public Battle
activation and reported a passed manual journey through player/Save Slot
setup, two structured battles and progress available after normal exit/reload.
**Core gameplay passed for that tested path;** capacity, backup/restore,
restart persistence and final Public Alpha readiness remain unverified. The
source default is fail-closed, while the installed VM has the explicit battle
opt-in. See `Public_Deployment_Runbook.md` and
`docs/Codex/Public_Core_Gameplay_Acceptance_2026-11-19.md`; this update did
not inspect the live VM.

## Major Components

- **Team Builder (Next.js):** gathers ordered teams, battle size, control and
  composition modes, optional seed, and the size-specific formation choice.
- **Live provider (Next.js):** the only HTTP-aware client module; creates a
  session, submits commands, validates envelopes, and normalizes failures.
- **Battle adapter (FastAPI):** validates public requests, uses seeded session
  randomness, maps formation plus ordered slots to hero positions, serializes
  snapshots/legal actions/events, and advances computer turns.
- **Progression store (SQLite):** owns exactly five local slots, their active
  selection, stable occupied-profile identities/metadata, per-profile unlocks,
  stage progress, and one-time rewards; it is separate from live sessions.
- **Combat engine (Python):** `Game`, `Hero`, `Skill`, status services, and
  concrete hero classes resolve all live rules.
- **Battle Screen (Next.js):** renders snapshots, queues supplied events, and
  uses a presentation-only formation registry for figure coordinates/depth.
- **Hero Gallery catalogue (Python + generated editorial registry):** extends
  the static roster response with deterministic skill-reference facts without
  constructing heroes or touching combat/session/RNG state. Human-editable
  YAML is strictly compiled into a typed frontend module before dev/build; its
  prose cannot author mechanics or structured numerical facts. Descriptive
  numbers may appear in prose but must be audited against the engine.
- **Manual formation demonstration (Python + Next.js):** an additive read-only
  catalogue evaluates every approved 2v2/3v3 attacker, classified direct-
  damage attack type, and relevant front-defeated scenario using pure Python
  helpers shared with live melee screening and position-damage adjustment.
  The Manual fetches it once, validates its shape, and selects supplied facts
  for display; it never creates a battle session or derives combat rules in
  React. The frontend formation registry supplies visual coordinates only.

### Development and public release boundary

`LOCT_RELEASE_MODE` accepts exact `development` or `public`; missing or invalid
values are public-safe. Local startup explicitly chooses Development. A public
frontend build uses a disposable source copy that omits the `/debug` Engineering
Test and `/assets` Asset Diagnostics pages before vinext discovers routes; the
shared Team Builder, Battle Screen, asset registry, engine, and adapter remain
in the main source and normal game. Stage Map Engineering navigation, hotspot
outlines, and the Battle viewport readout are Development-only presentation.
The backend registers Debug battle creation and the revision-bound
`POST /api/v1/debug/battles/{battleId}/auto-actions` only in explicit
Development; Public routing and OpenAPI omit both. Each auto request chooses
at most one friendly action through the existing specialization AI and legal
action path, then returns the normal battle envelope. The client may stop
issuing subsequent requests at a safe boundary, while an accepted action
finishes. No new Tactics Level or persistent Auto Battle state is introduced.
Player-authored team launch paths validate unique stable Hero Profession
definition IDs in the backend; enemy repeats and cross-side overlap remain
legal. These are deployment and launch-authority boundaries, not alternate
combat rules or save models.

### RELEASE-002 Batch 1 Public identity and save boundary

Development retains its anonymous schema-v4 progression database and battle
workflow. Public selects an explicit, separate schema-v5 SQLite database
outside the repository; it refuses missing, incompatible, or wrong-role
storage instead of creating or importing a replacement at runtime. An explicit
initialization step is required for a clean Public database. Public stores a
server-generated Player ID, non-unique case-preserving Player Name, keyed
Recovery Code verifier, one active revocable device session, rate-limit state,
five slots per player, and a player-specific active slot. Existing unlocks,
Stage progress, rewards, and Arena records remain profile-keyed, but Public
profile access is resolved through the authenticated player's owned slot.
Writes recheck the live session generation and ownership inside their SQLite
transaction. The browser never authors a Player ID or profile authority.

Public identity endpoints issue or recover a session and require explicit
saved-code acknowledgment before ordinary player access. Unsafe Public
mutations require exact configured Origin and session-bound CSRF verification;
the opaque authentication cookie is host-only, Secure, HttpOnly, SameSite=Lax.
The code is disclosed only at enrollment or authenticated replacement and is
not stored as plaintext. This paragraph describes Batch 1's foundation at
the time it was built; Batch 3 subsequently added onboarding, and the
2026-11-19 deployment established HTTPS ingress and start-screen rendering.
Neither milestone alone establishes Public Alpha acceptance.

Batch 1 deliberately removes **all** Public battle create, state, command,
preview, and completion routes from routing and OpenAPI. Generic
`POST /api/v1/battles` is absent in Public; Development retains its existing
generic, Stage, Arena, and Debug battle APIs. Schema-only battle lease,
diagnostic, and settlement tables do not activate those later lifecycle
features. Batch 2 must add battle ownership, capacity, expiry, Resign, seed
policy, and durable settlement before any Public battle route can reopen.

## Ownership Boundaries

| Concern | Authoritative owner |
|---|---|
| Team composition randomness, computer turns, target legality, damage, outcomes | Python adapter/engine |
| Hero `front`/`rear` position | Python adapter/engine |
| 2v2/3v3 formation selection input | Team Builder; validated and resolved by Python |
| Snapshot formation/position data | Python adapter |
| Per-combatant starting stat baseline, current battle stats, and signed net deltas | Python Hero instance / adapter |
| Figure anchors, scale, stacking, UI effects, accessibility | Next.js presentation registry |
| Browser display mode and shared actor browser-size rate | Next.js battle presentation configuration |
| Five-slot selection, training unlocks, stage progress, generic reward counts, Arena Run state | SQLite progression store / FastAPI |
| Profile naming/deletion, active-battle recovery, inventory/equipment, cloud/account saves | Not implemented |
| Gallery target semantics, classifications, numeric reference availability | Python static catalogue / audited registry |
| Gallery introductions, battle styles, skill prose, optional tips | Validated generated editorial content |
| Manual formation eligibility, direct-damage multiplier, result reasons, contextual rule explanation | Python static formation catalogue and shared live-rule helpers |

For new Gallery skills, the Python catalogue owns audited Base Damage/Healing,
target-dependent formula text, classifications, target semantics, and initial
cooldown counters. The frontend displays those facts using the shared Gallery
pattern and never duplicates combat calculation or cooldown logic. A formula
may name target Defence or Resistance without evaluating a target: the static
reference is distinct from the battle-specific preview. Follow the new-skill
checklist in `GDD/Skill_System.md` and validate the YAML/registry stable IDs
together with the catalogue.

The formation registry must never assign combat positions or decide legal
targets. Conversely, visual 3v3 depth is formation-, side-, and slot-specific
presentation data, not an additional Python gameplay state.

For read-only Battle Hero Stats inspection, each constructed Hero (including a
summon) retains a frozen, per-instance baseline after stat generation and
resistance compensation, before opening effects. The adapter serializes finite
current Damage, Defence, Agility, seven school resistances, and their signed
net differences without consuming RNG or altering combat. This presentation
baseline is separate from rule-bearing `original_*` fields. The browser never
recalculates those differences or queries a later combat state for inspection.

### Battle Scene responsive presentation

`web-ui/lib/battle/presentationConfig.ts` centrally classifies the live Battle
Scene by width, height, and orientation. It provides Monitor, Laptop Large,
Laptop Medium, Pad, Pad Mini, landscape Phone, and a portrait rotate-device
state without adding any Python/API field. The scene remains non-scrolling.

The Battlefield is the common projection context for arena background, combat
actors, combat VFX, and world-anchored UI. Screen HUD remains a distinct
responsibility. The effective actor scale is
`heroFigureScaleRate × formationScaleRate × battleSceneRate`. The scene rate is
the ratio of the current measured Battlefield background `cover` scale to its
1897×868 windowed reference scale, multiplied by the approved reference rate
`0.7`; it is not a fullscreen or viewport-mode override. Background source
dimensions are registered separately and custom images are measured on load.
Formation percentage
coordinates, depth, hero registry values, input geometry semantics, and all
combat authority remain unchanged.

## Data Flow

The ordinary live-battle path remains available in Development. RELEASE-002
Batch 2 adds owner-bound Public Stage/Arena routes for isolated testing only;
they are absent from a default Public process unless the server explicitly
sets `BATTLE_API_ENABLE_PUBLIC_BATTLES=1`. This is not Public-player launch
approval. Public never registers generic or Engineering Debug battle creation.

```text
Team Builder configuration
  → POST /api/v1/battles
  → FastAPI validation and seeded formation resolution
 → Hero construction with authoritative front/rear positions
  → Game session + snapshot/events/legal actions
  → ordered per-activation round-status HP journal
  → browser live provider
  → Battle Screen presentation queue and formation registry
```

Structured training uses a separate route: the UI obtains progression and the
server-owned curriculum/mode availability, then posts friendly selection,
required friendly formation, and its chosen `learner` or `tactics` mode to a
stage-battle route. The adapter supplies the fixed computer team/formation and
attaches stage, launch-profile, and immutable mode context to the session.
After an ended, authoritative friendly victory, a completion route performs
the active-profile SQLite transaction: Learner updates the sequential step
and any one-time reward; Tactics records only its separate battle completion.
A slot switch invalidates completion of the old session. This paragraph
describes the Development compatibility path; the isolated Public Batch 2
path binds Player ID, launch slot/profile, session generation, and route
context at creation, then commits terminal outcome and any Stage/Arena effect
before confirming Victory. Later completion calls read the original durable
receipt rather than grant again. No slot/stage/profile/reward field is added to
`BattleCreateConfiguration`.

Arena Run uses separate state, create, node-launch, and completion routes. The
client supplies only an initial six-definition owned squad, then the current
node's squad-limited friendly team and size-valid friendly formation. The store
owns the twelve-node schedule, enemy roster/formation, legacy node seed data,
current node, and completion receipts. A new player-intended node launch gets
a fresh server-owned combat seed; persisted node seeds no longer determine
retry combat. The optional profile-bound `attemptId` on Arena and structured
stage creation makes same-process transport retries return the original
session, while a new intentional launch uses a new ID. Its profile-scoped
abandon route removes only the
matching active run after the UI's explicit confirmation, so a new squad is
never created implicitly. `/api/v1/debug/battles` is a separate non-persistent
boundary for free-form testing and never uses the progression store; it is not
a flag on normal player battle creation.

For 2v2, the only formation IDs are `front-rear` and `side-by-side`; for 3v3,
they are `one-front-two-rear`, `two-front-one-rear`, and `all-front`. The
friendly formation is required for either size. A player-controlled enemy
supplies a matching-size formation; a computer enemy omits it and receives the
adapter's seeded selection. 1v1 has no formation fields.

### Isolated Public battle lifecycle (RELEASE-002 Batch 2)

The single-worker Public coordinator uses a per-player lock, then the battle
session lock, then a short SQLite transaction. SQLite is the reservation and
global-capacity authority: a provisional lease is inserted before RAM
construction, activated only after a fixed-ID session exists, and compensated
on construction/activation failure. One Player ID may have one active or
provisional battle; the initial global cap is 20 and the provisional TTL is
two minutes. The active inactivity deadline is 30 minutes from activation or
the completion of a newly accepted player action. State reads, previews,
rejected/duplicate commands, AI processing and presentation playback do not
extend it. A resolving marker prevents another request's lazy cleanup from
expiring an already accepted action. Resign, expiry and command resolution
share the owner-bound lifecycle; no browser-close signal is authoritative.

The engine session remains RAM-only and cannot resume after restart. Durable
diagnostics retain the effective 256-bit server combat seed as canonical hex,
immutable owner/launch context, lifecycle/outcome and receipt reference;
they do not store credentials or a full action replay. At terminal resolution,
one SQLite transaction verifies the launch binding, applies an authoritative
friendly Stage/Arena Victory effect (or none for Defeat/Draw), records the
original receipt, and releases the lease before confirmation. A failed
transaction does not confirm Victory and remains retryable while RAM survives.
An uncommitted engine result lost in a simultaneous storage failure and
process crash is not a confirmed Victory. The Public battle surface is
default-off in source when the explicit gate is absent. The Owner later
authorized and enabled it on the installed VM for core-gameplay acceptance;
remaining release gates stay open.
The expanded battle tables have an explicit Public battle-schema revision
marker; a Batch 1-shaped v5 database fails closed pending an approved offline
upgrade on a verified backup, never a silent runtime rewrite.

### Public client and operations boundary (RELEASE-002 Batch 3)

The Public frontend now resolves every player-facing API call on the same
origin, sends browser credentials, and holds the server-issued CSRF token and
one-time Recovery Code only in memory. `PublicSessionProvider` gates Stage Map
and Game routes on an acknowledged session; direct reload reads current
session without renewing it. A bounded explicit protected POST refreshes a
near-expiry session. Authentication failure clears the in-memory player view;
CSRF rejection revalidates read-only and does not replay an unsafe command.
Development preserves its anonymous local adapter path. Public Stage/Arena
battle launch, preview, command, Resign and receipt consume the Batch 2
owner-bound routes; a network-uncertain command retains its original command
ID. The source-level battle gate remains default-off without explicit opt-in;
the installed VM was separately opted in on 2026-11-19 after Owner authorization.

Offline `public_db_ops` uses SQLite online backup plus integrity/schema
checks, isolated no-overwrite restore, seven-daily and separate release
retention, and a narrowly verified backup-first marker upgrade in repository
tooling; it is not imported by the running API. The installed VM instead uses
`/usr/local/bin/loct-db-backup` with `loct-db-backup` systemd units. On
2026-11-20 the Owner reported a successful local snapshot and isolated
database-level restore, completing Stage 1 Database Protection within the
approved Alpha scope. Local backups share the VM/system disk with production
data; the Owner deferred GCS and accepted that correlated-loss risk for Alpha.
`deploy/public/` remains a template set, not an exact installed configuration.
Public health and identity fail closed on missing exact HTTPS Origin, Public
DB/schema, trusted proxy, or independent strong identity/rate keys. The Owner
reported Stage 2 Operational Stability complete for its defined resource,
controlled API/Web restart and logging checks. The Owner then accepted Stage 3
Nginx hardening, tested rate limiting and a Certbot renewal dry-run for Public
Alpha, selecting a Single-Release Strategy. Public SSH, local-only backups and
untested actual rollback are accepted residual risks. Unattended backup,
actual renewal/reload, VM reboot and in-progress battle recovery remain open;
Stage 4 was Owner-accepted and closed on 2026-11-23 after bounded production
10/20/30-player 2v2 tests at about 3 global RPS. The final 30-player run
settled 30/30 battles and a server snapshot observed 30 simultaneous active
leases. The installed battle-capacity setting changed from 20 to 200, but 200
is an operational ceiling, **not** proven sustainable capacity. Sustained
resource/SQLite stress and 50/100-player performance remain unmeasured. The
next gate was then described as a separate Final Public Alpha Launch Readiness
Review and Owner go/no-go decision. Under the Owner's 2026-11-27 roadmap
restructuring, that review is **Stage 5.3**, after Stage 5.1 RELEASE-004
deployment and Stage 5.2 actual rollback/redeployment; Stage 6 covers Public
Alpha publication. See `../Codex/Stage_5_and_6_Roadmap.md` for current gates
and `Public_Deployment_Runbook.md` for canonical operational evidence.

## Architectural Decisions

- The structured mode is a stage-route/session decision, not a stat, formation,
  or combat-rule variant. For a computer-controlled **enemy** in Learner, the
  adapter samples only its authoritative legal actions and valid target IDs
  with the session RNG; forced/skip paths remain governed by the engine.
  Tactics preserves the existing hero AI and legality reconciliation. Generic,
  Arena Run, Debug, and friendly automatic actors retain their prior policies.
- Structured stage access, per-campaign Tactics unlock, and per-mode completion
  are SQLite/backend authority. Existing stage records represent Learner
  history. The launch attempt fingerprint includes mode so one attempt ID
  cannot replay as a different mode; completion uses the session's mode rather
  than a client-supplied completion field.
- The creation/snapshot/event contract remains version `1.0`; formation fields
  are additive, size-discriminated values inside that contract.
- `Hero.position` defaults to `front` for legacy constructors, simulations,
  generators, and summons. Adapter-created 2v2/3v3 sessions pass the resolved
  value through the normal constructor chain.
- Approved attack-type target/damage rules stay in the engine. The UI consumes
  adapter `validTargetIds` and never infers protection of a rear hero. Mage
  Comprehensiveness, the approved Paladin skills, and the approved Priest
  skills follow the same dispatcher-to-`Hero.take_damage` path as the existing
  Warrior classifications; hybrid Penance passes the type only on its opponent
  damage branch.
- The 3v3 visual-depth correction is stored in the frontend trio registry so
  scale and stacking follow the approved per-side ordered-slot map without
  altering combat positions.
- The five local slots are intentionally unauthenticated and shared by clients
  pointed at the same adapter database. The backend active-slot reference is
  authoritative; browser state, URLs, and local storage are not. Schema-v1
  default progress migrates once into active slot 1. SQLite changes are
  transaction-safe, but battle sessions remain process-local; profile
  management, active-battle recovery, cloud sync, and multi-worker session
  recovery are deferred.

## Change Log

- 2026-11-18 — Documented RELEASE-002 Batch 3 Public client authority and
  offline/deployment-template boundaries; no live deployment was made.
- 2026-11-17 — Documented RELEASE-002 Batch 2's default-off isolated Public
  battle lifecycle, SQLite lease/terminal settlement boundary, and retained
  RAM-only engine sessions.
- 2026-11-10 — Documented explicit Development/Public Release Engineering
  isolation at frontend route discovery and backend route registration, while
  retaining one shared gameplay implementation.
- 2026-10-27 — Added immutable structured Learner/Tactics mode ownership,
  legal random enemy AI boundary, mode-specific persistence, and mode-bound
  attempt identity.
- 2026-08-15 — Documented the implemented UI-018/UI-019 cross-boundary
  formation architecture and the visual-depth ownership boundary.
- 2026-08-19 — Added the minimal SQLite-backed default-profile training
  progression boundary; it deliberately excludes profiles, inventory, and
  active-battle persistence.
- 2026-08-20 — Added the schema-v2 five-slot boundary, active-slot authority,
  safe legacy migration, and launch-profile guard for victory commits.
- 2026-08-31 — Added schema-v3 profile-scoped Arena Runs and a separate
  no-save-data debug creation boundary.
- 2026-07-26 — Initial authoritative architecture document created.
