# Screen Flow

## Purpose

Authoritative map of web-client screens, navigation, entry points, exits, and
important UI states.

## Current Implemented Flow

```text
Load application
  -> Startup Title Scene (/)
     -> START GAME (/stages)
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

## Agreed Startup and Profile Flow (Not Yet Implemented)

The following flow is agreed product design for the future persistent
player-data/save system. It supersedes the current direct `START GAME` → Stage
Map entry only when the corresponding backend-authoritative profile and save
implementation is explicitly authorised. Persistence details live in
[Player Data and Save System](../Technical/Player_Data_and_Save_System.md).

```text
Start Page
  -> [ START ]
     -> hide/remove START
     -> [ NEW GAME ] [ CONTINUE GAME ]

NEW GAME
  -> create player profile with a stable profile ID
  -> assign default initial roster/progression
  -> persist player record
  -> make profile active
  -> Stage Map

CONTINUE GAME
  -> list saved player profiles
  -> select profile
     -> no unfinished battle: load profile -> Stage Map
     -> unfinished battle: show saved-battle summary
        -> [ RESUME BATTLE ] -> load authoritative saved state -> Battle page
        -> [ ABANDON BATTLE ] -> confirmation
           -> Cancel: retain battle summary
           -> Confirm: end/remove unfinished battle -> Stage Map
```

Initial display names may use a simple sequence such as `Player 1`, `Player 2`,
and `Player 3`, but a stable internal profile ID—not the display name—identifies
the profile. New Game assigns the initial roster/progression through the
backend; the client does not author persistent state.

Continue Game lists all saved local profiles. If none exist, it must be disabled
or show a clear **No saved games** state; exact visual presentation is an
implementation decision. When an unfinished battle exists, the summary should
identify useful context such as stage/training name and round (for example,
`Warrior's Barrack`, `Defensive Training`, `Round 4`).

Abandon Battle must ask for confirmation before destroying the unfinished
battle, for example:

```text
Abandon the current battle?
Your progress in this battle will be lost.

[ CANCEL ] [ ABANDON BATTLE ]
```

Confirmed abandonment removes/ends only the active unfinished battle. It does
not award that battle's completion or unlock rewards and does not remove
previously earned permanent player progress. Future PvP disconnect/reconnect/
forfeit flow is out of scope.

## Screen Inventory

### Stage Selection

`/stages` is the presentation-only Valley of Champions selector between the
title scene and Team Builder. It renders the one owner-supplied map at
`/game-images/Stage_Map/valley_of_champions.png` in an intrinsic `1672 / 941`
map container. Stage geometry is percentage-based inside that same container,
not the viewport.

Arena and Warrior's Barrack are currently enabled. Each uses the same
map-bound pointer hover and keyboard-focus treatment, and click, Enter, or Space
navigation. Arena opens `/game?stage=arena`. Warrior's Barrack opens
`/game?stage=warriors-barrack` through a percentage-based hotspot over the
left-side red-banner fortress. Mage's Tower, Rogue's Forest, Paladin's Altar,
and Priest's Cathedral remain inactive configuration metadata only; they render
no controls, labels, effects, or state treatment. Local development may add
`?debugHotspots=1` to outline enabled-stage geometry; normal and production
presentation leave it off.

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
- for 2v2 only, a friendly **Front and Rear** / **Side by Side** formation
  choice; the enemy choice is editable only when enemy control is Player;
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

The formation selector uses stable values `front-rear` and `side-by-side` and
shows the resulting Hero 1/Hero 2 position labels. For a computer-controlled
enemy, Team Builder shows an explanation instead of an editable selector and
omits `enemyFormation`; Python returns its seeded choice through combatant
snapshot positions. Formation controls and fields are absent in 1v1 and 3v3.

Warrior's Barrack uses the same Team Builder in a separate structured-stage
mode. It is a temporary in-memory training sequence, not a profile, save,
unlock, reward, or campaign system. The builder exposes only its approved
four-definition player Matrix (Warrior Weapon Master, Mage Comprehensiveness,
Priest Comprehensiveness, and Rogue Comprehensiveness), its fixed battle
format, and an accessible immutable predefined enemy summary. Arena-style
battle-size, enemy composition, enemy-control, seed, and enemy-team controls
are absent from structured mode.

The current ordered Warrior's Barrack sequence is:

1. Battle 1 — 2v2 against Warrior Defence and Priest Comprehensiveness.
2. Battle 2 — 1v1 against Warrior Weapon Master.
3. Battle 3 — 3v3 against Warrior Defence, Warrior Berserker, and Priest
   Comprehensiveness.

Battle 1 uses the same friendly 2v2 formation selector. Its predefined enemy
team remains immutable and computer-controlled, so the enemy formation is
chosen authoritatively and represented by the same non-editable explanation.
Battles 2 and 3 show no formation controls.

The exact fixed-team request continues to use the existing battle-create
contract. The client validates that every configured definition is supplied by
the adapter roster before revealing the builder; missing definitions show a
retryable configuration/roster error rather than a substitute hero.

### Battle Screen

Renders the selected live formation and authoritative snapshot. All friendly
heroes are player-controlled. Enemy turns are either submitted by the player or
resolved by the adapter through existing Python AI, according to the Team
Builder configuration.

For 2v2, each side's two supplied `position` values plus ordered combatant
slots select the approved percentage coordinate pair independently. A
Front-and-Rear side has one `front` and one `rear`; a Side-by-Side side has two
`front` combatants. Duel and trio coordinates are unchanged. Target
selectability comes exclusively from the current legal action's
`validTargetIds`, even when a supplied valid target is `rear`.

The Battle Log presents ordered, sanitized lines authored by Python through the
battle-info and status-update channels. Typed battle events remain the source
for animation and state reconciliation; equivalent generic event text is hidden
to avoid duplicate lines without suppressing the typed event itself.

### Completion Dialog

Appears only when the authoritative snapshot phase is `ended`. It announces the
outcome, initially focuses its action, and contains keyboard Tab focus. Arena
returns to its Team Builder. In Warrior's Barrack, the typed authoritative
outcome drives the action: a friendly victory advances Battle 1 → 2 → 3, and
the third victory returns to `/stages`; enemy victory, draw, and round-limit
results show **Retry Battle** and return to preparation for that same battle.
No result is inferred from a log line or visual label.

### Asset Gallery

Development/reference route at `/assets`; it is not part of the normal battle
flow. Its return link navigates directly to `/game`.

## Navigation Rules

### Current Implementation

- `/` opens the non-interactive cinematic startup title scene.
- `/stages` opens the stage-selection map without creating a battle session.
- `/game` opens Arena Team Builder after the roster loads; `/game?stage=arena`
  identifies Arena configuration mode.
- `/game?stage=warriors-barrack` starts the temporary Warrior's Barrack
  sequence at Battle 1 preparation.
- `START GAME` navigates to `/stages`; Arena, Warrior's Barrack, and the Asset
  Gallery return link navigate through their documented destinations.
- Team Builder launches only live Python-backed sessions.
- Mock fixtures remain test/development data and are not the normal user entry
  flow.
- Battle state is not retained when returning to Team Builder. Warrior's
  Barrack retains only its current sequence position in client memory while the
  page remains active; completing Battle 3 clears it by returning to the Stage
  Map.
- Browser reload during a battle does not resume the process-local session and
  may restart or lose the temporary Warrior's Barrack sequence.

### Agreed Persistence Design

- The future Start action opens New Game / Continue Game choices rather than
  entering Stage Map immediately.
- New Game creates, persists, and activates a profile before Stage Map.
- Continue Game loads a selected profile, then opens Stage Map or offers Resume
  Battle / Abandon Battle for its unfinished PvE/training battle.
- Resume returns directly to the saved Battle page from backend-authoritative
  state. Abandonment requires confirmation and returns to Stage Map after the
  backend ends/removes only that unfinished battle.

## Error, Empty, and Loading States

- Roster loading: `Loading approved heroes…`
- Roster/API failure: `HERO ROSTER UNAVAILABLE` with Retry.
- Battle creation failure: existing battle-service error boundary with Retry.
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
