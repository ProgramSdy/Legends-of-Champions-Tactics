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
  routes to `/stages`.
- The control uses dark forged-metal/gunmetal material, a restrained
  antique-gold border, subtle blue-violet accent, dimensional bevel, pale text,
  and clear hover, pressed, and focus-visible states. It is not a flat
  application-style button or a high-glow decorative element.
- Title animation is limited to a restrained page/logo/control entrance and
  hover transition. It honours reduced-motion preferences. Decorative startup
  artwork is hidden from screen readers; the logo has descriptive alternative
  text and the start control remains keyboard accessible.

### Stage Selection

- `/stages` presents the owner-supplied Valley of Champions map as a dominant,
  undistorted 16:9 visual. The map and its overlays share an intrinsic map
  frame; stage coordinates must use percentages of that frame rather than
  viewport pixels.
- Arena and Warrior's Barrack are enabled locations. Their hover and focus
  state uses a modest warm gold/orange radial illumination, a soft pulse,
  visible focus outline, and compact frontend-rendered stage-name / `Available`
  label. Warrior's Barrack geometry covers the left-side red-banner fortress.
  The treatment remains an overlay and must not alter the source map.
- The crossed-swords cursor is scoped to enabled stage controls and falls back
  to a normal crosshair when a browser cannot load the cursor image. It must not
  change the global cursor or appear over inactive landmarks.
- Inactive locations remain unlabelled and visually untouched: no control,
  lock, desaturation, glow, cursor, or completion/progression treatment.
- Development-only hotspot debug may expose enabled-stage boundaries for
  geometry tuning. It is off by default and unavailable in production.

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
- The formation registry is the single source for presentation coordinates.
  Duel retains its established coordinates. The approved 2v2 pairs are
  percentage anchors inside the unmodified battlefield: Front and Rear is
  friendly `(42,68)` / `(22,68)` and enemy `(59,68)` / `(78,68)` in ordered
  slots; Side by Side is friendly `(33,54)` / `(33,85)` and enemy `(68,54)` /
  `(68,85)`. These correspond to the owner reference's pink 1/2 and 3/4 plus
  green 1/2 and 4/3 locations; numbered reference markers never render.
- Approved 3v3 ordered anchors are: One Front, Two Rear friendly `(42,68)` /
  `(28,80)` / `(28,53)` and enemy `(59,68)` / `(73,53)` / `(73,80)`; Two
  Front, One Rear friendly `(42,54)` / `(42,81)` / `(23,67)` and enemy
  `(59,81)` / `(59,54)` / `(78,67)`; All Front friendly `(39.5,52)` /
  `(39.5,71)` / `(39.5,90)` and enemy `(60.5,90)` / `(60.5,71)` /
  `(60.5,52)`. These are percentage interpretations of the three supplied
  owner references; their colored numbered markers never render.
- A duo figure's `front`/`rear` depth label comes from the combatant snapshot.
  In a trio, combat `front`/`rear` remains snapshot-owned, but the visual
  nearest/middle/furthest depth order is explicitly keyed by formation, side,
  and ordered slot. It must not be inferred solely from front/rear: nearest is
  larger and renders above middle, which renders above furthest. The figure's
  HP/status panel, aura, effects, and target hit area share that figure layer.
- Crowded Side by Side and trio anchors may declare a formation-local horizontal
  HP/status-panel lane. The panel remains inside its own figure layer and keeps
  its scale-aware vertical clearance; the lane prevents a nearer/lower panel
  from obscuring adjacent figure art. This is presentation-only and must not
  alter combat positions, targetability, effects, or figure depth.
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
- Formation layers follow the approved presentation-depth registry. For 3v3:
  One Front, Two Rear is friendly 2/1/3 and enemy 3/1/2 nearest-to-furthest;
  Two Front, One Rear is friendly 2/3/1 and enemy 1/3/2; All Front is friendly
  3/2/1 and enemy 1/2/3. This visual order is independent of the combat
  front/rear position, and keeps nearer figures and attached health boxes above
  farther figures.

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

## Team Builder

- Keep the Battle Rules control bar's labels, native radio/input semantics,
  validation, and visual treatment stable when changing surrounding layout.
- Show distinct formation selectors for 2v2 and 3v3, never a mixed option set.
  They use native radio inputs, visible focus, blue friendly and red enemy
  selected treatments, and explicit ordered Hero `Front`/`Rear` labels. A
  computer-controlled enemy shows a readable size-specific non-editable
  explanation instead of a selected-looking control. Three-option controls use
  three columns when space permits and stack to one column at 720px or below.
- Use blue player-slot treatment and red enemy-slot treatment. The active
  player or specified-enemy slot has a visible side-appropriate selected state;
  Hero Selection Matrix cards visibly indicate the hero assigned to that slot.
- Current Stage previews use the supplied Stage Map image in a clipped,
  `object-fit: cover` frame. Crop focus derives from canonical stage geometry;
  source artwork must never be stretched or replaced.
- Player slots and matrix cards use a fixed, bounded media frame with the
  shared asset fallback chain. A missing portrait must remain readable and
  never expose a browser broken-image icon.
- Narrow layouts stack team slots and retain a two-column Hero Selection Matrix
  without horizontal document overflow.
- Always display three Hero positions on both teams. Positions beyond battle
  size are visibly subdued and unavailable to focus, assignment, selection, or
  submission; team-card borders and focus treatments retain bottom clearance.
- Team Builder identity is profession-only: show `Faculty · Specialization`,
  never a roster catalogue or runtime hero name. Faculty controls derive from
  the received roster and Matrix navigation pages only the active result set.

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
- 2026-08-08 — Added map-bound Valley of Champions stage-selection standards
  and updated the startup entry flow to `/` → `/stages` → `/game`.
- 2026-08-09 — Added UI-013 Team Builder slot, matrix, current-stage crop, and
  protected Battle Rules presentation standards.
- 2026-08-10 — Added Warrior's Barrack's active map-hotspot treatment while
  retaining the existing Arena and inactive-landmark visual rules.
- 2026-08-14 — Added the UI-018 2v2 formation-control language, approved
  snapshot-driven percentage coordinate pairs, responsive selector stacking,
  and the prohibition on numbered reference markers.
- 2026-08-15 — Added the three UI-019 3v3 formation option sets, owner-reference
  percentage anchors, snapshot-owned depth, and responsive three-choice
  selector treatment while keeping duel and duo placement stable.
- 2026-08-15 — Clarified the approved formation/side/slot-specific 3v3 visual
  depth, scale, and stacking order after the UI-019 depth correction.
- 2026-08-15 — Added formation-local overhead panel lanes for crowded 2v2 and
  3v3 layouts; panels stay attached to their figure layer while avoiding
  adjacent hero art.
