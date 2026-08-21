# Screen Flow

## Purpose

Authoritative map of web-client screens, navigation, entry points, exits, and
important UI states.

## Current Implemented Flow

```text
Load application
  -> Startup Title Scene (/)
     -> START GAME
        -> NEW GAME / LOAD GAME dialog
           -> NEW GAME -> choose one of five slots
              -> empty slot: create and activate -> Stage Selection
              -> occupied slot: confirm overwrite -> replace and activate -> Stage Selection
           -> LOAD GAME -> choose occupied slot -> activate -> Stage Selection
        -> Stage Selection
           -> Arena (/game)
              -> Load approved roster from GET /api/v1/heroes
                 -> Loading state
                 -> Retryable roster error
                 -> Team Builder
                    -> Validate configuration
                    -> Create live battle
                       -> Retryable battle-service error
                       -> Battle Screen
                          -> Authoritative battle completion
                          -> Completion dialog
                          -> Return to Team Builder
```

Returning to Team Builder unmounts the battle subtree and discards the live
provider, battle ID, authoritative snapshot cache, presentation queue, timers,
event log, selections, and completion-dialog state. A later launch creates a
new provider and API session.

## Implemented Five-Slot Startup Flow

The startup client lists exactly five backend-owned local save slots. It does
not navigate to Stage Map until a create, load, or confirmed-overwrite action
returns the selected active slot and its authoritative progression. Details live in
[Player Data and Save System](../Technical/Player_Data_and_Save_System.md).

```text
Start Page
  -> [ START ]
     -> [ NEW GAME ] [ LOAD GAME ]

NEW GAME
  -> list Slots 1-5
  -> empty slot: create exact starter progression -> select active -> Stage Map
  -> occupied slot: exact-slot overwrite warning
     -> Cancel: no write -> slot selector
     -> Confirm: replace only that slot -> select active -> Stage Map

LOAD GAME
  -> list Slots 1-5 with empty slots disabled
  -> occupied slot: select active without reset -> Stage Map
```

LOAD GAME is disabled with a readable **No saved games** explanation when all
five slots are empty. The dialog supports Escape/Cancel, keyboard-only slot
selection, contained/restored focus, loading status, and retryable errors. The
client submits only the slot action; it never submits starter heroes, stage
progress, or rewards. Profile naming/deletion and unfinished-battle recovery
remain deferred.

## Screen Inventory

### Stage Selection

`/stages` is the presentation-only Valley of Champions selector between the
title scene and Team Builder. It renders the one owner-supplied map at
`/game-images/Stage_Map/valley_of_champions.png` in an intrinsic `1672 / 941`
map container. Stage geometry is percentage-based inside that same container,
not the viewport.

Arena, Warrior's Barrack, and Paladin's Altar are currently enabled. Each uses the same
map-bound pointer hover and keyboard-focus treatment, and click, Enter, or Space
navigation. Arena opens `/game?stage=arena`. Warrior's Barrack opens
`/game?stage=warriors-barrack` through a percentage-based hotspot over the
left-side red-banner fortress. Mage's Tower, Rogue's Forest, Paladin's Altar,
and Priest's Cathedral remain inactive configuration metadata only; they render
no controls, labels, effects, or state treatment. Local development may add
`?debugHotspots=1` to outline enabled-stage geometry; normal and production
presentation leave it off.

UI-020 supersedes the preceding inactive-Altar sentence: Paladin's Altar opens
`/game?stage=paladins-altar` through the bright right-middle altar hotspot.
Mage's Tower, Rogue's Forest, and Priest's Cathedral remain inactive.

### Team Builder

The playable application entry point is `/game`. Direct or invalid stage-query
visits use Arena configuration mode. Arena provides:

- battle size: 1v1, 2v2, or 3v3;
- three fixed visual hero positions per team. Positions beyond the selected
  battle size are visibly disabled, non-focusable, and never submitted; active
  player positions remain keyboard-operable Matrix assignment targets;
- random or player-specified enemy composition;
- Matrix-assigned enemy positions per required slot in specified mode;
- Python-engine computer control or player control for the enemy team;
- for 2v2, a friendly **Front and Rear** / **Side by Side** formation choice;
- for 3v3, a separate friendly **One Front, Two Rear** / **Two Front, One
  Rear** / **All Front** choice; in either size, the enemy choice is editable
  only when enemy control is Player;
- an optional non-negative integer seed;
- a Current Stage preview, Back to Stage Map control, and every definition
  supplied by the adapter roster endpoint in the Hero Selection Matrix.

The Team Builder keeps its header/stage preview, Battle Rules, team panels,
Hero Selection Matrix, and launch footer in normal document flow. At reduced
viewport heights, its existing vertical scroll area reveals lower sections;
team cards are not compressed or allowed to overlap the Matrix.

Team Builder shows only faculty and specialization for player slots, enemy
slots, Matrix cards, and specified-enemy options; it does not expose catalogue
or runtime hero names. The roster-derived All/faculty filter and bounded
previous/next Matrix paging assign the selected player slot or, in
specified-enemy mode, the selected enemy slot. Player and specified-enemy
slots start empty and show a clear selection prompt until assigned. Random
enemy selection remains Python-owned and is never changed by the matrix.
When the session is created, Python assigns runtime display names from the
relevant faculty pools while stable definition and combatant IDs continue to
identify selections, targets, and commands.

The launch action is disabled until all required selectors and seed input are
valid. Repeated definitions and overlap between teams are permitted because no
authoritative design rule currently prohibits them.

The 2v2 selector uses stable values `front-rear` and `side-by-side`. The 3v3
selector instead uses `one-front-two-rear`, `two-front-one-rear`, and
`all-front`. Each option shows every ordered Hero slot's Front/Rear position.
For a computer-controlled enemy, Team Builder shows the size-specific
explanation instead of an editable selector and omits `enemyFormation`; Python
returns its seeded choice through the snapshot formation and combatant
positions. Formation controls and fields remain absent in 1v1.

Structured training uses the same Team Builder in a persisted, backend-owned
mode. Warrior's Barrack and Paladin's Altar each use a nine-battle curriculum,
fixed enemy teams and formations, and server-authoritative access and rewards.
The builder exposes only the player heroes unlocked for the active save slot,
its fixed battle format, and an accessible immutable predefined enemy summary.
Arena-style battle-size, enemy-composition, enemy-control, and enemy-team
controls are absent from structured mode. A seed remains optional where the
stage contract permits it.

Structured 2v2 and 3v3 battles expose the same friendly formation selectors as
Arena, while 1v1 hides them. Predefined enemy teams and formations stay
immutable and computer-controlled, and their formation is shown as a fixed
note. The client validates that the server curriculum matches its presentation
configuration before revealing the builder; a mismatch or missing roster
definition shows a retryable configuration/roster error rather than a
substitute hero.

### UI-020 Persistent Structured Training

Warrior's Barrack and Paladin's Altar each render the approved nine-battle curriculum,
Battle N of 9, a player-selectable size-valid formation, immutable ordered enemy
team with fixed formation, reward context,
and nine accessible completed/available/locked steps. The player Matrix uses
only `unlockedHeroDefinitionIds` from progression; fixed enemies continue to
resolve through the full static roster even while player-locked.

Launch uses the one-based stage route and sends only the chosen player team,
the selected player formation when applicable, and optional seed. A friendly
victory is committed through the backend completion route, followed by fresh
progression/stage fetches. A non-victory retries the same step. A newly granted
reward opens a focus-contained notification with the backend message; Continue
then opens the next permitted step or Stage Map. Replay with no new grant does
not reopen the notification. Storage, contract, launch, commit, and refetch
failures remain visible and retryable.

### Battle Screen

Renders the selected live formation and authoritative snapshot. All friendly
heroes are player-controlled. Enemy turns are either submitted by the player or
resolved by the adapter through existing Python AI, according to the Team
Builder configuration.

For 2v2, each side's two supplied `position` values plus ordered combatant
slots retain the approved coordinate pair independently. For 3v3, each side's
snapshot formation selects one approved presentation registry and the ordered
slots select its three anchors and formation-specific visual depth. That depth
is not inferred from a hero's supplied combat `position`. Duel and duo
coordinates remain unchanged. Target
selectability comes exclusively from the current legal action's
`validTargetIds`, even when a supplied valid target is `rear`.

The Battle Log presents ordered, sanitized lines authored by Python through the
battle-info and status-update channels. Typed battle events remain the source
for animation and state reconciliation; equivalent generic event text is hidden
to avoid duplicate lines without suppressing the typed event itself.

### Completion Dialog

Appears only when the authoritative snapshot phase is `ended`. It announces the
outcome, initially focuses its action, and contains keyboard Tab focus. Arena
returns to its Team Builder. In either structured stage, the typed
authoritative outcome drives the action: a friendly victory is committed by
the backend and opens the next permitted battle; the ninth committed victory
returns to `/stages`. Enemy victory, draw, and round-limit results show
**Retry Battle** and return to preparation for that same battle. No result is
inferred from a log line or visual label.

### Asset Gallery

Development/reference route at `/assets`; it is not part of the normal battle
flow. Its return link navigates directly to `/game`.

## Navigation Rules

### Current Implementation

- `/` opens the cinematic title scene. START GAME opens the five-slot New Game /
  Load Game dialog without navigating.
- `/stages` opens the stage-selection map without creating a battle session.
- `/game` opens Arena Team Builder after the roster loads; `/game?stage=arena`
  identifies Arena configuration mode.
- `/game?stage=warriors-barrack` and `/game?stage=paladins-altar` open the
  respective persisted curriculum at its next permitted battle.
- A successful create, load, or confirmed overwrite navigates to `/stages`.
  Arena, both structured stages, and the Asset Gallery return link navigate
  through their documented destinations.
- Team Builder launches only live Python-backed sessions.
- Mock fixtures remain test/development data and are not the normal user entry
  flow.
- Battle sessions are process-local and are not resumed after a browser reload.
  Completed structured battles, access state, unlocked heroes, and rewards
  persist in the backend active save slot; a new launch reloads that state and
  starts the next permitted battle.

### Deferred Persistence Design

- Active-battle checkpoint, Resume Battle, and Abandon Battle are not part of
  the implemented five-slot flow.
- Profile names, rename/delete controls, accounts, cloud sync, and online
  identity remain deferred.

## Error, Empty, and Loading States

- Roster loading: `Loading approved heroes…`
- Roster/API failure: `HERO ROSTER UNAVAILABLE` with Retry.
- Battle creation failure: existing battle-service error boundary with Retry.
- Save-slot listing/action failure: visible startup-dialog error with retry or
  the original slot action still available; no navigation or local fallback.
- Invalid Team Builder configuration: precise inline validation and disabled
  launch.
- Ended Arena battle: modal outcome and Return to Team Builder.
- Ended Warrior's Barrack battle: modal continuation, Stage Map return, or
  Retry Battle according to the supplied authoritative outcome.

## Change Log

- 2026-07-29 — Documented UI-002 Team Builder, live multi-team battle, and
  return/reset flow.
- 2026-07-26 — Initial document created.
- 2026-07-31 — Documented UI-006 player selection labels, runtime battle names,
  and the Python-authored Battle Log presentation boundary.
- 2026-08-05 — Added the startup title scene at `/` and direct playable route
  at `/game`.
- 2026-08-08 — Inserted the Valley of Champions `/stages` selector between the
  title scene and Team Builder; Arena is the sole enabled destination.
- 2026-08-09 — Reworked Team Builder around visual team slots and the Hero
  Selection Matrix; Stage Map now passes only the selected Arena presentation
  context to `/game`.
- 2026-08-10 — Added agreed, not-yet-implemented New Game / Continue Game,
  profile, resume, and abandonment flow; cross-referenced the authoritative
  player-data/save design.
- 2026-08-10 — Activated the temporary Warrior's Barrack three-battle
  structured training sequence without persistence or battle API changes.
- 2026-08-14 — Added 2v2-only formation selection, computer-enemy formation
  explanation, structured Battle 1 compatibility, and authoritative
  snapshot-position battlefield placement.
- 2026-08-15 — Added the three size-specific 3v3 formation choices, computer
  explanation, structured Battle 3 selection, typed request handoff, and
  snapshot-formation-driven trio placement.
- 2026-08-19 — UI-020 documented Paladin's Altar, persistent nine-battle
  training, authoritative roster gating, locked steps, completion commits,
  reward feedback, and retryable progression failures.
- 2026-08-20 — UI-021 replaced direct startup navigation with the accessible
  five-slot New/Load/confirmed-overwrite flow and active-slot refresh boundary.
