# Screen Flow

## Purpose

Authoritative map of web-client screens, navigation, entry points, exits, and
important UI states.

## Current Flow

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

## Screen Inventory

### Stage Selection

`/stages` is the presentation-only Valley of Champions selector between the
title scene and Team Builder. It renders the one owner-supplied map at
`/game-images/Stage_Map/valley_of_champions.png` in an intrinsic `1672 / 941`
map container. Stage geometry is percentage-based inside that same container,
not the viewport.

Only Arena is currently enabled. Its pointer hover and keyboard focus reveal a
restrained warm overlay and label, and its click, Enter, and Space activation
navigate to `/game`. Warrior's Barrack, Mage's Tower, Rogue's Forest, Paladin's
Altar, and Priest's Cathedral exist as inactive configuration metadata only;
they render no controls, labels, effects, or state treatment. Local development
may add `?debugHotspots=1` to outline Arena geometry; normal and production
presentation leave it off.

### Team Builder

The playable application entry point at `/game`. It provides:

- battle size: 1v1, 2v2, or 3v3;
- one player-team selector per required slot;
- random or player-specified enemy composition;
- one enemy-team selector per required slot in specified mode;
- Python-engine computer control or player control for the enemy team;
- an optional non-negative integer seed;
- the eight definitions supplied by the adapter roster endpoint.

Player-team selectors identify choices as `Faculty - Specialization` and do
not expose catalogue roster names as if they were fixed battle identities.
Player-specified enemy selectors retain catalogue name plus specialization.
When the session is created, Python assigns runtime display names from the
relevant faculty pools while stable definition and combatant IDs continue to
identify selections, targets, and commands.

The launch action is disabled until all required selectors and seed input are
valid. Repeated definitions and overlap between teams are permitted because no
authoritative design rule currently prohibits them.

### Battle Screen

Renders the selected live formation and authoritative snapshot. All friendly
heroes are player-controlled. Enemy turns are either submitted by the player or
resolved by the adapter through existing Python AI, according to the Team
Builder configuration.

The Battle Log presents ordered, sanitized lines authored by Python through the
battle-info and status-update channels. Typed battle events remain the source
for animation and state reconciliation; equivalent generic event text is hidden
to avoid duplicate lines without suppressing the typed event itself.

### Completion Dialog

Appears only when the authoritative snapshot phase is `ended`. It announces the
outcome, initially focuses the Return action, contains keyboard Tab focus, and
returns to Team Builder.

### Asset Gallery

Development/reference route at `/assets`; it is not part of the normal battle
flow. Its return link navigates directly to `/game`.

## Navigation Rules

- `/` opens the non-interactive cinematic startup title scene.
- `/stages` opens the stage-selection map without creating a battle session.
- `/game` opens Team Builder after the roster loads.
- `START GAME` navigates to `/stages`; Arena and the Asset Gallery return link
  navigate to `/game`.
- Team Builder launches only live Python-backed sessions.
- Mock fixtures remain test/development data and are not the normal user entry
  flow.
- Battle state is not retained when returning to Team Builder.
- Browser reload during a battle does not resume the process-local session.

## Error, Empty, and Loading States

- Roster loading: `Loading approved heroes…`
- Roster/API failure: `HERO ROSTER UNAVAILABLE` with Retry.
- Battle creation failure: existing battle-service error boundary with Retry.
- Invalid Team Builder configuration: precise inline validation and disabled
  launch.
- Ended battle: modal outcome and Return to Team Builder.

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
