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

### Startup Title Scene

- The initial `/` route is a full-viewport cinematic title scene. It uses the
  owner-supplied startup artwork as a crop-safe direct public image and a
  subtle readability-only vignette; it must not materially obscure the battle
  artwork.
- The supplied logo retains its aspect ratio in the upper centre. The
  `START GAME` control is centered below the logo in clear artwork space and
  routes to `/game`.
- The control uses dark forged-metal/gunmetal material, a restrained
  antique-gold border, subtle blue-violet accent, dimensional bevel, pale text,
  and clear hover, pressed, and focus-visible states. It is not a flat
  application-style button or a high-glow decorative element.
- Title animation is limited to a restrained page/logo/control entrance and
  hover transition. It honours reduced-motion preferences. Decorative startup
  artwork is hidden from screen readers; the logo has descriptive alternative
  text and the start control remains keyboard accessible.

### Battlefield Health Panels

- Battlefield health/status panels sit above their associated hero figure.
- In 1v1, the entire overhead health/status box is 1.5× its shared logical
  size, anchored from its bottom edge. 2v2 and 3v3 retain the shared size.
- Its vertical clearance is calculated from the hero's measured frame height
  and formation scale, so each health/status box remains 12px above the visible
  figure frame.
- The runtime hero name is part of the health/status box, above the HP meter;
  it is truncated rather than allowed to overlap the figure or other UI.
- Format-specific spacing must not move the hero figure, formation anchor, or
  target-control hit area.

### Battle Formations

- Hero figures must read as grounded on the arena floor in every live format.
- The formation registry is the single source for slot coordinates. Current
  vertical anchors are 80% for duel; 82% and 100% for duo; and 75%, 88%, and
  100% for trio. Within duo and trio, the lower (nearer) slot uses the larger
  scale so visual depth agrees with the ground position.
- Duel figures use scale 1.5. The two duel teams retain matching y and scale
  values so their presentation remains symmetric.
- Format scaling must preserve clear separation between figures, overhead
  health panels, side panels, and the command deck.
- Final figure artwork uses contained, bottom-aligned presentation without the
  placeholder silhouette clip. Friendly artwork preserves its original
  orientation; enemy artwork is horizontally mirrored without mirroring its
  label, aura, health/status panel, or target hit area.
- Direct final artwork and fallback figures use one 172px-wide, bottom-aligned
  logical frame before formation scaling. A final image sets its frame height
  from its intrinsic aspect ratio; missing or failed artwork uses the 202px
  fallback frame. The aura is centered from that frame; 1v1 opposing figures
  share its feet baseline.
- `web-ui/lib/battle/assets.ts` owns a per-definition battlefield figure-scale
  registry. Owner-approved per-hero values adjust only that hero's battlefield
  art, attached target control/aura/effects, and HP-panel position. Portraits,
  side cards, and game rules are unaffected; unknown definitions use `1.0`.
- Overhead health/status UI must retain 12px of visible separation above the
  dynamic figure frame in every format.
- Stackable status icons show a centered yellow numeral inside the icon's
  lower-right corner, without a badge fill, border, or separate focus/click
  target. The numeral retains the established readable size and expands only
  for `99+`. Show valid counts including `1`; suppress zero, absent, or invalid
  counts. The status tooltip and accessible name retain the exact authoritative
  count in both overhead and Team Information icon sizes.
- Formation layers follow depth: rear is below centre, and centre is below
  front, so a nearer front figure and its health box cannot be covered by a
  farther slot.

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

- Healing feedback is green and anchored to the authoritative event target.
- Authoritative `statusPresentation: "buff"` uses blue double rings;
  `"debuff"` uses red double rings. Neutral or unrelated status events do not
  invent a local gameplay classification.
- Friendly lunge feedback moves right; enemy lunge feedback moves left. It is
  presentation-only and must not alter formation or combat positions.
- Battlefield auras are side-owned: friendly figures are blue and enemy
  figures are red. An acting figure retains its side color and adds the normal
  pulse animation; purple is not an active-aura color.
- While a selected skill still requires targets, every valid battlefield target
  uses a crosshair cursor, regardless of side. The cursor returns to normal
  once the required maximum target count is selected; multi-target skills keep
  the crosshair until all targets are selected.
- Desktop Team Builder and Battle Asset Registry scrolling uses a finite,
  focusable region with a stable right-side scrollbar gutter when overflowing.
- Battle entry is a non-interactive overlay on the composed battlefield. The
  `3`, `2`, and `1` frames share one centered layout box, font metrics,
  transform origin, and animation; `START` uses its separate intentional label
  treatment. The overlay preserves an accessible live-status announcement and
  must honour reduced-motion preferences.

## Accessibility

_To be documented._

## Change Log

- 2026-07-26 — Initial document created.
- 2026-07-30 — Documented format-specific battlefield health-panel clearance.
- 2026-07-31 — Documented UI-006 grounded formations, complete profession
  labels, full-height skill cards, square skill artwork, and readable battle-log
  typography.
- 2026-08-01 — Documented final battlefield-art containment and enemy-only
  image mirroring.
- 2026-08-02 — Documented UI-007 shared figure/aura alignment, target-bound
  effect language, side-aware lunge direction, and desktop scroll behavior.
- 2026-08-02 — Documented the owner-authorised UI-007 follow-up that doubled
  the shared figure footprint while preserving independent HP-panel clearance.
- 2026-08-02 — Corrected duo/trio depth-scale ordering so nearer, lower
  formation positions render larger than farther positions.
- 2026-08-02 — Enlarged the complete 1v1 overhead health/status box to 1.5×,
  bottom-anchored above the hero; 2v2 and 3v3 remain unchanged.
- 2026-08-02 — Added valid-target crosshair feedback that persists until a
  selected skill's required target count is complete.
- 2026-08-03 — Reduced scale-aware HP-panel clearance to 4px, moved runtime
  names into the HP panel, established rear/centre/front stacking, and made
  active aura animation retain its team color.
- 2026-08-04 — Made battlefield frames follow supplied hero artwork’s
  intrinsic aspect ratio, retained a 202px frame for missing/failed images,
  and anchored HP/status panels 8px above the resulting dynamic frame.
- 2026-08-04 — Increased the dynamic HP/status panel clearance to 12px.
- 2026-08-04 — Added the per-definition battlefield figure-scale registry;
  all supported definitions initially use the neutral `1.0` ratio.
- 2026-08-02 — Documented the UI-008 in-scene countdown metric contract and
  accessible non-interactive entry state.
- 2026-08-05 — Added the cinematic startup title-scene visual and interaction
  standard for the `/` → `/game` entry flow.
