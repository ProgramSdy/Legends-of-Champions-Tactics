# Technical Architecture

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

## Ownership Boundaries

| Concern | Authoritative owner |
|---|---|
| Team composition randomness, computer turns, target legality, damage, outcomes | Python adapter/engine |
| Hero `front`/`rear` position | Python adapter/engine |
| 2v2/3v3 formation selection input | Team Builder; validated and resolved by Python |
| Snapshot formation/position data | Python adapter |
| Figure anchors, scale, stacking, UI effects, accessibility | Next.js presentation registry |
| Five-slot selection, training unlocks, stage progress, generic reward counts | SQLite progression store / FastAPI |
| Profile naming/deletion, active-battle recovery, inventory/equipment, cloud/account saves | Not implemented |

The formation registry must never assign combat positions or decide legal
targets. Conversely, visual 3v3 depth is formation-, side-, and slot-specific
presentation data, not an additional Python gameplay state.

## Data Flow

```text
Team Builder configuration
  → POST /api/v1/battles
  → FastAPI validation and seeded formation resolution
  → Hero construction with authoritative front/rear positions
  → Game session + snapshot/events/legal actions
  → browser live provider
  → Battle Screen presentation queue and formation registry
```

Structured training uses a separate route: the UI obtains progression and the
server-owned curriculum, then posts only friendly selection/required friendly
formation to a stage-battle route. The adapter supplies the fixed computer
team/formation and attaches stage plus launch-profile context to the session.
After an ended, authoritative friendly victory, a completion route performs the
active-profile SQLite transaction that records the step and any one-time reward
before returning updated progression. A slot switch invalidates completion of
the old session. No slot/stage/profile/reward field is added to
`BattleCreateConfiguration`.

For 2v2, the only formation IDs are `front-rear` and `side-by-side`; for 3v3,
they are `one-front-two-rear`, `two-front-one-rear`, and `all-front`. The
friendly formation is required for either size. A player-controlled enemy
supplies a matching-size formation; a computer enemy omits it and receives the
adapter's seeded selection. 1v1 has no formation fields.

## Architectural Decisions

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

- 2026-08-15 — Documented the implemented UI-018/UI-019 cross-boundary
  formation architecture and the visual-depth ownership boundary.
- 2026-08-19 — Added the minimal SQLite-backed default-profile training
  progression boundary; it deliberately excludes profiles, inventory, and
  active-battle persistence.
- 2026-08-20 — Added the schema-v2 five-slot boundary, active-slot authority,
  safe legacy migration, and launch-profile guard for victory commits.
- 2026-07-26 — Initial authoritative architecture document created.
