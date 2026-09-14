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
  opens the local save dialog; it never routes before a save action succeeds.
- The control uses dark forged-metal/gunmetal material, a restrained
  antique-gold border, subtle blue-violet accent, dimensional bevel, pale text,
  and clear hover, pressed, and focus-visible states. It is not a flat
  application-style button or a high-glow decorative element.
- Title animation is limited to a restrained page/logo/control entrance and
  hover transition. It honours reduced-motion preferences. Decorative startup
  artwork is hidden from screen readers; the logo has descriptive alternative
  text and the start control remains keyboard accessible.
- The save flow uses one modal surface for New Game/Load Game and the five-slot
  selectors. Empty/occupied/active states use text in addition to colour. Load
  is disabled with an explanation when no occupied slot exists. The destructive
  warning names the exact slot and pairs a neutral keep action with a distinct
  red overwrite action.
- Modal focus begins on the first useful action, remains trapped, returns to
  START on close, and supports Escape. At narrow widths, choice cards and all
  five slot cards stack into one scrollable column without horizontal overflow.

### Stage Selection

- `/stages` presents the owner-supplied Valley of Champions map as a dominant,
  undistorted 16:9 visual. The full-viewport frame clips a centred intrinsic
  map canvas; stage coordinates use percentages of that canvas rather than
  viewport pixels, so hover regions remain aligned when edge scenery crops.
- Arena, Warrior's Barrack, and Paladin's Altar are enabled locations. Their hover and focus
  state uses a modest warm gold/orange radial illumination, a soft pulse,
  visible focus outline, and compact frontend-rendered stage-name / `Available`
  label. Warrior's Barrack geometry covers the upper-left red-banner fortress;
  Paladin's Altar covers the bright upper-right altar landmark.
  The treatment remains an overlay and must not alter the source map.
- The crossed-swords cursor is scoped to enabled stage controls and falls back
  to a normal crosshair when a browser cannot load the cursor image. It must not
  change the global cursor or appear over inactive landmarks.
- Inactive locations remain unlabelled and visually untouched: no control,
  lock, desaturation, glow, cursor, or completion/progression treatment.
- Development-only hotspot debug may expose enabled-stage boundaries for
  geometry tuning. It is off by default and unavailable in production.
- Stage Map navigation controls sit above map art without changing hotspot
  geometry: a restrained home/title icon at upper left and a semi-transparent
  spanner icon for Engineering Test & Debugging at upper right. Both retain
  visible focus and dark-fantasy forged-metal styling.

### Battlefield HP HUD

- The battlefield HP HUD is transient: only an authoritative `damageApplied`
  or `healingApplied` event for that hero shows it. It also appears for
  zero-damage and full-HP healing events; status-only and damage-prevented
  events do not show it.
- The HUD appears 300ms before the HP mutation, remains through the meter
  transition, and remains a further 300ms before disappearing. In 1v1, the
  entire overhead HP box is 1.5× its shared logical size, anchored from its
  bottom edge. 2v2 and 3v3 retain the shared size.
- Its vertical clearance is calculated from the hero's measured frame height
  and formation scale, so each HP box remains 12px above the visible
  figure frame.
- The runtime hero name is left-aligned beside the HP meter in 10px text and
  is truncated rather than allowed to overlap the figure or other UI. The HUD
  contains no status-icon row; status icons remain in Team Information cards.
- Format-specific spacing must not move the hero figure, formation anchor, or
  target-control hit area.

### Battle Formations

- The Battle Scene is a non-scrolling landscape presentation. Its responsive
  owner is `presentationConfig.ts`, which assigns one named display mode and
  one `browserSizeRate`; components must not add independent viewport checks.
  Portrait is a contained rotate-device state, not a portrait battle layout.
- The battlefield separates world background, combat actors, VFX, and
  world-anchored UI from the screen HUD. Only world responsibilities share the
  formation projection; headers, side panels, command deck, controls, and
  dialogs never scale together as a full-screen canvas.
- At the 1920×1080 Monitor reference, browser size rate is `1.0`. Final actor
  scale is hero rate × formation rate × browser rate. Do not use that browser
  rate to move formation X/Y anchors, retune formation depth, alter target
  legality, or resize source-owned hero metadata.

- Hero figures must read as grounded on the arena floor in every live format.
- The formation registry is the single source for presentation coordinates.
  Duel retains its established coordinates. The approved 2v2 pairs are
  percentage anchors inside the unmodified battlefield: Front and Rear is
  friendly `(42,68)` / `(22,68)` and enemy `(59,68)` / `(78,68)` in ordered
  slots; Side by Side is friendly `(33,54)` / `(33,85)` and enemy `(68,54)` /
  `(68,85)`. These correspond to the owner reference's pink 1/2 and 3/4 plus
  green 1/2 and 4/3 locations; numbered reference markers never render.
- **Owner-approved 2v2 visual-scale decision (2026-08-28):** Front and Rear
  uses `1.04` for every friendly and enemy figure. Side by Side keeps the
  upper/far figure at `0.94` and uses `1.04` for the lower/near figure on both
  sides. These presentation multipliers are applied to each hero's separate
  per-definition figure scale; they do not change combat positions, targeting,
  damage, or the underlying artwork registry.
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
  transient HP HUD, aura, effects, and target hit area share that figure layer.
- Every battlefield HP HUD is horizontally centred directly above its
  own hero artwork in duel, duo, and trio layouts. It remains inside the hero's
  figure layer and uses the measured artwork height, combined hero/formation
  scale, and 12px vertical clearance. Formations must not offset panels into
  separate horizontal lanes.
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

- Generic healing feedback is green and anchored to the authoritative event
  target. Priest healing retains its soft-gold treatment and caster runes;
  Paladin healing uses a bright, soft white-gold/sun-gold descending target
  blessing that settles into a restrained ground glow. Each ordered
  status-phase HP event receives its own feedback—never a net-change animation.
- Consecutive same-target, same-type HP events retain one committed idle frame
  between presentations. This deliberately restarts CSS motion and floating
  text, so two damage ticks produce two shakes and two damage numbers.
- Authoritative `statusPresentation: "buff"` uses blue double rings;
  `"debuff"` uses red double rings. Neutral or unrelated status events do not
  invent a local gameplay classification.
- Friendly lunge feedback moves right; enemy lunge feedback moves left. It is
  presentation-only and must not alter formation or combat positions.
- Battlefield auras are side-owned: friendly figures are blue and enemy
  figures are red. An acting figure retains its side color and adds the normal
  pulse animation; purple is not an active-aura color.
- While a selected skill still requires targets, every valid battlefield target
  uses a crosshair cursor, regardless of side. The cursor and gold selection
  glow apply only while its bounded target control is hovered or focused—not
  the larger transparent figure layout wrapper. The cursor returns to normal
  once the required maximum target count is selected; multi-target skills keep
  the crosshair until all targets are selected. In a genuine overlap of two
  target controls, the approved higher visual-depth figure receives pointer
  input.
- Desktop Team Builder, Arena Run hub/squad builder, and Battle Asset Registry
  scrolling uses a finite, focusable region with a stable right-side scrollbar
  gutter when overflowing. The Battle Scene itself remains non-scrolling.
- Battle entry is a non-interactive overlay on the composed battlefield. The
  `3`, `2`, and `1` frames share one centered layout box, font metrics,
  transform origin, and animation; `START` uses its separate intentional label
  treatment. The overlay preserves an accessible live-status announcement and
  must honour reduced-motion preferences.

## Accessibility

_To be documented._

### Pre-Alpha Sound Feedback

- Sound is supplementary feedback only. Controls, target legality, effects,
  status, and outcomes must remain visually and semantically complete with
  audio unavailable or muted by the browser.
- Startup, Stage Map, Team Builder, Arena Run, Battle, Debug, and Asset Registry
  share one application-root click and hover/focus convention. Enabled native
  buttons, links, form controls and associated labels participate by semantic
  role; accessible custom controls explicitly opt in with
  `data-audio-feedback="interactive"`. Disabled, `aria-disabled`, hidden,
  inert, decorative, and noninteractive content remains silent.
- Hover is one quiet cue per pointer/focus entry, uses the central cooldown,
  and must not retrigger from pointer movement inside the same control. Pointer,
  touch, Enter, and Space activation receive one restrained click cue without
  changing native behavior. Associated labels and controls are one sound target
  so a radio/checkbox activation cannot double-play. Typing, input changes,
  scrolling, rerenders, and passive form-state changes never infer additional
  cues.
- Browser sound initializes lazily after a trusted interaction. Autoplay
  rejection, missing browser audio APIs, provider loading failure, and playback
  failure are silent failures and must never block interaction or presentation.
  A browser without sticky user-activation reporting may omit opening sounds
  until the first eligible pointer, touch, or keyboard activation.
- Pre-alpha procedural sounds stay low/moderate in volume and distinct by
  function: restrained mechanical UI click, quieter high tick for hover,
  notification chime for the battle-start event, energetic skill cue, short impact,
  upward evade, rising buff, descending debuff, and heavier defeated impact.
- Ordered battle sounds follow authoritative active presentation events. Never
  infer sound from HP/status snapshots, log prose, rerenders, or client-side
  classification. Neutral/unknown status presentation remains silent.

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
  `object-fit: cover` frame. Preview focus/scale/offset comes from explicit
  enabled-stage metadata separate from hotspot geometry; source artwork must
  never be stretched or replaced. Arena retains its centre crop, Warrior's
  Barrack focuses the left red-banner building, and Paladin's Altar focuses the
  right-middle altar at both desktop and narrow widths.
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
- Structured Team Builder uses nine progression buttons: nine columns at
  desktop and three at narrow width. Locked buttons are native-disabled with
  explicit accessible names; completed, available, and current states do not
  rely on color alone.
- Structured 2v2 and 3v3 battles use the same friendly formation radio
  controls as Arena; their predefined enemy formation remains a readable fixed
  note. Structured 1v1 hides formation controls. Only backend-returned
  `newlyGrantedRewards` opens the focus-contained reward
  notification, which announces the backend message and focuses Continue.

## Change Log

- 2026-09-14 — Extended the centralized `ui.click` / `ui.hover` language to
  every current player-facing route through one SSR-safe application-root
  boundary, with semantic eligibility, custom-control opt-in, label/control
  deduplication, and disabled/decorative/typing anti-spam rules. Ordered battle
  event sounds remain a separate presentation-queue-only boundary.
- 2026-09-12 — Added the AUDIO-001 pre-alpha sound language: one lazy,
  replaceable browser audio boundary, scoped click/hover accessibility cues,
  ordered event-driven battle feedback, authoritative status classification,
  and per-ID spam/deduplication safeguards.
- 2026-09-11 — Added compact Battle Information Transparency previews:
  server-authored immediate range, target HP, evasion-only Hit Chance, and
  separately labelled material effects appear on legal target hover/focus. The
  information layer is pointer-transparent, pins in compact landscape, and
  clears for stale, unavailable, automatic, targetless, and unsupported state.

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
- 2026-08-19 — UI-020 added the Altar hotspot, responsive locked-step grid,
  fixed-formation note, and accessible one-time reward notification language.
- 2026-08-20 — UI-021 added the accessible five-slot startup dialog/overwrite
  treatment and separate responsive preview-focus metadata for Arena, Barrack,
  and Altar.
- 2026-08-28 — Recorded the owner-approved 2v2 formation visual-scale tuning:
  equal `1.04` Front and Rear figures, and `0.94` upper/far plus `1.04`
  lower/near Side by Side figures.
- 2026-08-29 — Replaced crowded-formation panel lanes with a shared rule that
  centres every battlefield HP/status panel directly above its own hero while
  preserving measured-height, scale-aware 12px vertical clearance.
- 2026-08-29 — Replaced permanent battlefield health/status panels with the
  event-only HP HUD: 300ms lead/trailing windows, a left-aligned 10px name,
  and no battlefield status-icon row.
- 2026-08-30 — Made figure layout wrappers pointer-transparent and retained
  pointer interaction only on the bounded target control, so far 3v3 figures
  remain selectable outside genuine target-control overlaps.
