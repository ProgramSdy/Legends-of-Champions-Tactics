# Current Task

## Status

Ready for implementation — mandatory pre-code boundary report

---

## Task ID

UI-024

## Title

Establish a Layered, Height-Aware Responsive Architecture for the Battle Scene

## Objective

Refactor only the Battle Scene presentation into a clear responsive foundation
for Monitor, Laptop Large, Laptop Medium, Pad, Pad Mini, and landscape-phone
configurations—without redesigning those final layouts now and without changing
the approved 1920×1080 battle presentation.

## Background

The current battle page is a non-scrolling CSS grid rooted at
`BattleScreen.tsx` / `.battle-shell`. It uses `height: 100dvh`,
`min-width: 1180px`, and grid rows for header, battle layout, command deck,
and controls. The battle layout has two fixed-width Team Information panels
and a central `.battlefield`. Current compact rules are width-only media
queries at 1600px, 1450px, and 1370px; there is no battle-specific height or
orientation configuration system.

The battlefield already has conceptual layers, but their responsibilities are
not yet made explicit for responsive work: `.battlefield` background/pseudo
overlays, formation-slot figure actors, effect layers, figure-attached world
UI, and the screen-space header/side panels/command deck/controls. This task
makes those boundaries clear without requiring five new physical root nodes.

The current, owner-tuned hero figure scale is exactly:

```
current figure scale = formationScale × heroFigureScaleFor(definitionId)
```

`formationScale`, coordinate anchors, and presentation depth come from
`web-ui/lib/battle/formations.ts`; hero-specific rates come from the stable
`heroFigureScales` registry in `web-ui/lib/battle/assets.ts`. The Battle Screen
passes the computed scale through `--figure-scale`; Python remains authoritative
for combat positions, legality, skills, damage, events, and outcomes. These
contracts were tuned at 1920×1080 and must remain intact.

## Mandatory Pre-Code Boundary Report

Before editing implementation files, Core must inspect the current source and
send the project owner a concise report containing all ten items below:

1. Battle-scene files/components/styles in scope.
2. Current hero-scale calculation and its implementation location.
3. Current formation-scale calculation and its implementation location.
4. Current hero-position calculation and its implementation location.
5. Current battle layout/viewport structure.
6. Current width/height responsive rules affecting the battle scene.
7. Exact proposed scope boundary.
8. Minimal implementation plan.
9. Risks to the existing 1920×1080 appearance.
10. How 1920×1080 before/after equivalence will be verified.

The report must explicitly state that source-owned hero scales, formation
coordinates/scales/depth, and Python combat logic will not be retuned. After
the report establishes this boundary, implementation may begin only within the
requirements below.

## Requirements

### 1. Five conceptual presentation responsibilities

1. Establish and document a clear responsive responsibility boundary for:
   - **Arena / World Background:** arena artwork and controlled crop/scale only.
   - **Combat Actors:** heroes and future summons/temporary actors placed in
     the battlefield coordinate system.
   - **Combat VFX:** projectiles, spells, hits, ground effects, and other
     world-space effects.
   - **World-Anchored UI:** actor-following target controls/markers, transient
     HP HUD, floating numbers, casting indicators, and related presentation.
   - **Screen UI / HUD:** header/round/turn chrome, team panels, command deck,
     skills, battle log, speed/auto/select/resign controls, and dialogs.
2. Physical DOM changes are permitted only where they clarify ownership. Do
   not create five wrapper elements merely to mirror the conceptual list.
3. World background, actors, VFX, and world-anchored UI must share the
   Battlefield Viewport/projection context. Screen HUD must stay conceptually
   separate and must not be scaled as one 1920×1080 page canvas.
4. Do not move combat authority, skill/legal-target logic, events, outcomes,
   or formation decision-making into presentation code.

### 2. Preserve exact hero and formation tuning

1. Preserve every existing `heroFigureScales` value, fallback behavior,
   `formationScale` value, formation coordinate, ordered slot, depth, figure
   frame calculation, target-control geometry, and enemy mirror behavior.
2. Introduce only one shared responsive presentation factor:

   ```
   final figure scale = heroFigureScaleRate × formationScaleRate × browserSizeRate
   ```

   `browserSizeRate` is configuration/viewport-owned; it is neither hero- nor
   formation-specific. It must be centrally expressed (preferably a battle CSS
   custom property consumed at the existing figure-scale boundary), never
   copied into definition metadata or individual formations.
3. At the 1920×1080 reference configuration, `browserSizeRate` is exactly
   `1.0`; therefore computed final figure scales, relative hero sizes, and all
   formation-specific relationships match the pre-task result exactly.
4. Browser-size scaling applies to actor presentation only. It must not become
   a blanket multiplier for formation X/Y coordinates, tactical positions,
   pointer legality, or screen-HUD layout.

### 3. Battlefield projection and responsive configuration foundation

1. Define a stable Battlefield Viewport/reference-projection boundary for
   world-space actors, VFX, and anchored UI. Existing formation percentages
   remain reference positions and are mapped into the current battlefield
   viewport; no formation meanings or adapter-authored positions may change.
2. Prepare one small, understandable display-configuration system considering
   width, height, and orientation. Its initial categories are:
   - Monitor: width ≥1600 and height ≥900.
   - Laptop Large: approximately 1440–1599 with adequate height around 800+.
   - Laptop Medium: approximately 1180–1439 with adequate height around 700+.
   - Pad: approximately 900–1179 landscape.
   - Pad Mini: approximately 700–899 landscape.
   - Phone: landscape only, strongly identified by short height, approximately
     550px or below.
3. Treat these as starting categories, not a demand to implement six finished
   visual designs or a matrix of width × height rules. A wide, short viewport
   must be distinguishable from a wide, tall viewport for future dense HUD
   behavior.
4. Prefer CSS custom properties, `clamp()`, and a small number of genuine
   layout breakpoints. If runtime JavaScript is needed for a named display
   mode, centralize it in one battle-presentation boundary; do not scatter
   independent viewport checks among components. Do not add a library.
5. Keep the battle screen non-scrolling. Do not solve responsiveness through
   document scrolling, broad `min-width` overflow, or scaling every HUD region
   together. Establish controlled HUD-density variables/slots and a minimum
   usable battlefield area for later work, without redesigning skill cards or
   HUD content in this task.
6. Support landscape phone as an architectural configuration. Do not build a
   portrait-phone battle layout; establish a contained rotate-device state only
   if necessary to prevent an unusable portrait game screen.

### 4. 1920×1080 regression lock

1. At 1920×1080, preserve the current visual result and behavior: actor size,
   relative hero size, formation scale/depth/position, arena composition/crop,
   header and side-panel arrangement, command deck, controls, HUD spacing,
   animations/VFX, target interactions, and gameplay.
2. Do not perform unrelated visual cleanup, hero/formation retuning, text
   edits, asset/art changes, source reorganization, or component renames.
3. Any baseline difference that cannot be directly justified as essential to
   the responsive architecture is a regression and must be removed.

## Out of Scope

- Any screen other than the live Battle Scene: Team Builder, Squad Builder,
  Arena Run hub, debug page, Stage Map, startup/save flow, assets/gallery, and
  all non-battle routes.
- Python/FastAPI logic; game/hero/skill/status data; battle rules, legal
  actions, targeting, formation logic, damage, events, AI, persistence,
  Arena/Stage logic, and API/data contracts.
- Changes to approved hero-specific scales; 2v2/3v3 coordinates, scales, or
  depth; target hit-area behavior; transient HP HUD timing/content; or any
  UI-022 work previously discarded by the owner.
- Full visual redesign of the six target configurations, portrait-phone battle
  layout, new art/assets, or unrelated code cleanup.
- Editing the owner-controlled
  `docs/web-ui/screenshots_debug/UI_Review_Human.md`.

## Relevant Files

### Primary Battle Scene scope

- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/app/globals.css` — battle-shell/layout/viewport/figure/VFX/HUD rules
- `web-ui/lib/battle/formations.ts`
- `web-ui/lib/battle/assets.ts`
- focused new presentation configuration/projection module only if warranted

### Existing regression tests and documentation

- `web-ui/tests/battle-screen.test.tsx`
- `web-ui/tests/ui-007-regressions.test.tsx`
- `web-ui/tests/ui-019-formations.test.tsx`
- `web-ui/tests/hero-figure-scales.test.tsx`
- `web-ui/tests/quick-hp-hud.test.tsx`
- focused new responsive-architecture tests and baseline evidence
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/web-ui/Style_Guide.md`
- `docs/Technical/Architecture.md`
- `docs/Codex/Completed.md`

## Acceptance Criteria

1. Core provides the mandatory ten-item pre-code boundary report before
   implementation work, accurately identifying the existing Battle Screen,
   CSS grid/breakpoints, `heroFigureScaleFor`, and formation registry boundary.
2. The Battle Scene has documented/enforced conceptual separation between
   world background, actors, VFX, world-anchored UI, and screen HUD without
   forcing unnecessary DOM complexity or moving any gameplay ownership.
3. A small height- and orientation-aware responsive configuration foundation
   exists for all six named categories, without broad scrolling or a finished
   redesign of every category.
4. The central scale path supports exactly one `browserSizeRate` factor, whose
   reference result at 1920×1080 is 1.0. All per-hero and per-formation inputs,
   relative results, and position semantics remain unchanged.
5. World actor/VFX/anchored UI projection is distinct from screen-HUD density
   handling. Browser-size scaling does not multiply existing formation X/Y
   positions or alter authoritative combat positions/legality.
6. The current 1920×1080 page is visually and functionally equivalent before
   versus after in every listed regression-lock item; no unrelated screen,
   data, backend, Team Builder, Arena, asset, text, or battle-rule change is
   present.
7. Landscape phone is accounted for without a portrait battle layout. Existing
   desktop and compact-width behavior is retained until a later task explicitly
   authorizes final per-configuration layouts.

## Validation Required

### Automated

1. Add focused tests for the centralized configuration boundary: width + height
   category selection or CSS variable contract, landscape/portrait handling,
   reference `browserSizeRate: 1`, and no scattered component-level viewport
   behavior.
2. Add/retain tests proving exact current hero scale multiplication, all
   formation registry positions/scales/depth, figure frame/HP-HUD anchoring,
   target-control contracts, VFX layering, and Battle Screen interaction.
3. Add a 1920×1080 baseline regression test/snapshot/style assertion that
   proves the reference mode uses the prior grid/scale/position values. If
   pixel screenshots are used, capture comparable before/after evidence with
   the same fixture, browser, zoom, DPR, and deterministic battle state.
4. Run affected/frontend full suites, TypeScript typecheck, ESLint, production
   build, and task-scoped `git diff --check`. Record exact commands/results and
   distinguish pre-existing failures.

### Manual browser validation

1. Capture a deterministic 1920×1080 baseline before modifying the Battle
   Scene, then compare the same 1v1, 2v2, and 3v3 fixtures after implementation
   at the same browser zoom/DPR. Verify every regression-lock item explicitly.
2. Inspect representative Monitor, Laptop Large, Laptop Medium, Pad, Pad Mini,
   and short landscape-phone viewports. Confirm non-scrolling behavior, clear
   battlefield/HUD responsibility boundaries, no unintended positioning or
   scale retune, and no horizontal-overflow workaround masquerading as layout.
3. Verify portrait phone is not treated as a full supported battle layout.
   If a rotate-device state is implemented, confirm it is accessible, contained,
   and appears only for portrait/unsupported small configurations.
4. Exercise battle opening, automatic turns, skill targeting/multi-target,
   HP/combat/VFX presentation, fullscreen, completion/resign dialogs, keyboard
   controls, and reduced-motion behavior at the reference viewport. Record
   console/network/runtime errors.

## Documentation/Handoff Requirements

- Update `WEB_UI_ARCHITECTURE.md`, `Style_Guide.md`, and Technical Architecture
  with the exact five conceptual layers, configuration ownership, scale formula,
  1920×1080 invariants, non-scrolling/density direction, and deferred final
  configuration designs.
- Append UI-024 completion evidence to `Completed.md`: pre-code report,
  changed files, exact behavior added, explicitly unchanged behavior, test/build
  results, 1920×1080 comparison evidence, known risks, and remaining six-layout
  work.

## Agent Assignments

### Complexity and risk

**High-risk frontend architectural refactor.** It must make future responsive
work safer while preserving finely tuned desktop geometry. Primary risks are a
hidden reference-scale change, accidental formation-coordinate scaling,
background/HUD coupling, global scrolling/overflow, duplicated viewport logic,
and visual regression to battle interaction or effects.

### Participating agents

- `project-manager` — first produce the mandatory boundary report, enforce
  scope, coordinate baseline evidence and documentation, and prevent scope
  expansion into non-battle systems.
- `ui-developer` — own the Battle Screen/CSS presentation boundaries, central
  configuration variables/resolver, reference-projection foundation, and
  responsive accessibility without retuning visual inputs.
- `test-automator` — own deterministic 1920×1080 before/after evidence,
  viewport/configuration regressions, scale/position preservation, interaction,
  reduced-motion, and build/test results.
- `reviewer` — independently compare the reference output and audit scale,
  coordinates, layer ownership, overflow/non-scroll behavior, documented
  deferred scope, and absence of non-battle changes.
- `game-engine-developer` — confirm no Python/API/contract modification is
  necessary; do not alter engine or adapter behavior for this task.

## Completion Notes

Do not mark UI-024 complete until the pre-code report and all selected role
reports are available; reference 1920×1080 comparison evidence establishes no
unapproved visual/behavior difference; focused and full frontend validation is
recorded; and docs state exactly what foundation was added versus what final
responsive designs remain deferred.
