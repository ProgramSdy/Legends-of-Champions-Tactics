# UI Style Guide

## Purpose

Authoritative visual and interaction standards for the project's web UI.

## Visual Direction

_To be agreed and documented._

## Colour

_To be documented._

## Typography

_To be documented._

## Spacing and Layout

_To be documented._

## Components

_To be documented._

### Battlefield Health Panels

- Battlefield health/status panels sit above their associated hero figure.
- The enlarged 1v1 figure treatment uses additional vertical clearance:
  `.format-duel .overhead` is positioned at `top: -20px`.
- The shared 2v2 and 3v3 overhead position remains `top: -5px`.
- Format-specific spacing must not move the hero figure, formation anchor, or
  target-control hit area.

### Battle Formations

- Hero figures must read as grounded on the arena floor in every live format.
- The formation registry is the single source for slot coordinates. Current
  vertical anchors are 55% for duel; 48% and 62% for duo; and 44%, 55%, and
  66% for trio.
- Format scaling must preserve clear separation between figures, overhead
  health panels, side panels, and the command deck.

### Battle Side Cards

- Non-summoned heroes show the complete profession as
  `Faculty · Specialization` beside the stable runtime display name.
- Summoned units keep the explicit `Specialization · Summon` treatment.

### Command Deck

- Skill cards stretch to the full height of the command-deck skills region.
- Skill artwork remains square at every supported breakpoint. Placeholder
  cards use deliberate decorative treatment rather than an empty lower strip.
- Battle-log body copy is 11px at the primary desktop layout and no smaller
  than 10px at the compact desktop breakpoint.

## Interaction and Feedback

_To be documented._

## Accessibility

_To be documented._

## Change Log

- 2026-07-26 — Initial document created.
- 2026-07-30 — Documented format-specific battlefield health-panel clearance.
- 2026-07-31 — Documented UI-006 grounded formations, complete profession
  labels, full-height skill cards, square skill artwork, and readable battle-log
  typography.
