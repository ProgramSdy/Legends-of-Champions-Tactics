# Current Task

**Status:** Completed

**Task:** AUDIO-002 — Extend Shared UI Sound Feedback to All Player-Facing Scenes

**Owner request date:** 2026-09-14

## Objective

Extend the completed AUDIO-001 centralized frontend audio system beyond the
Battle Screen. Apply its existing `ui.click` and `ui.hover` feedback across all
current player-facing web scenes, using one reusable application-level or
scene-level integration pattern. Do not duplicate jsfxr/audio-manager logic in
individual components and do not change the established battle-event sounds.

## Background

AUDIO-001 created `web-ui/lib/audio/` with the browser-safe `AudioManager`,
typed sound definitions, and battle-specific event mapper. Testing confirms
that its effects currently appear only in the Battle Screen because
`useBattleAudio` is attached there. The owner has now requested audio feedback
in all scenes.

This is an extension of the existing pre-alpha sound language, not a new sound
system. Existing sound IDs, lazy trusted-interaction unlock, quiet failure,
cooldowns, and battle presentation queue ownership must remain authoritative.

## Requirements

### 1. One shared UI-feedback integration

- Reuse `AudioManager` and the existing `ui.click` / `ui.hover` IDs. Do not
  import `jsfxr` outside `web-ui/lib/audio/` and do not create a second audio
  manager, per-screen audio instances, document-global browser listeners, or
  per-component preset definitions.
- Extract or adapt the generic UI part of the existing Battle Screen audio hook
  into a clearly named reusable client boundary/hook. It must be safe for
  Next.js SSR/hydration and use the same singleton manager and central
  cooldown/deduplication behaviour.
- Scope delegated pointer/focus/keyboard handling to an explicit application
  or scene root, using a deliberate marker/convention for eligible controls.
  It must not add sound to decorative, disabled, inaccessible, hidden, or
  noninteractive elements.
- A normal pointer, keyboard, or touch interaction must unlock audio safely.
  Hover/focus use the quiet `ui.hover` cue once on entry; a real activation
  uses `ui.click` once. Enter/Space must not produce an extra click on top of
  the browser’s normal follow-up click event.
- Audio failures, unsupported browser APIs, and autoplay restrictions must
  remain silent and never prevent navigation, form submission, stage selection,
  save actions, battle creation, or any other normal UI action.

### 2. Required scene coverage

Apply the shared UI feedback convention to all existing player-facing routes
and their interactive dialogs/overlays. Cover the currently shipped controls
that are eligible at runtime, including:

| Scene/route | Required eligible controls |
| --- | --- |
| Startup `/` | START GAME, New/Load/Retry/Cancel, save-slot choices, overwrite/confirmation actions. |
| Stage Map `/stages` | Enabled stage hotspots, title route, and Engineering/Test-Debugging route. Inactive artwork remains silent and noninteractive. |
| Team Builder / standard battle entry | Back route, Battle Rules inputs, formation selectors, player/enemy hero slots, Hero Selection Matrix/cards, pagination/filter controls, random/enemy controls, seed input where interactive, and ENTER BATTLE. |
| Arena Run | Hub/squad-builder choices, hero selection, node/run actions, back/return controls, give-up confirmation, and completion acknowledgement. |
| Battle Scene | Preserve AUDIO-001 battle event sounds and current marked controls. Refactor only as needed so it uses the shared UI feedback boundary without duplicate click/hover sounds. |
| Debug and Battle Asset Registry | Their available navigation, setup, retry, and normal action controls. Development routes remain functional but do not gain battle-event sound inference. |

- Inspect actual routes/components before editing. If a named control is not
  present in the current product, document that fact rather than inventing UI.
- Use `ui.hover` only for interactive pointer-entry and keyboard-focus feedback.
  Avoid scroll/drag/input-change noise, focus loops, repeated pointer movement,
  and sound on disabled controls. Text typing and passive form state changes
  must not create click/hover spam.
- Existing battle semantic sounds (`battle.event`, `battle.skill`,
  `battle.damage`, `battle.evade`, `battle.buff`, `battle.debuff`, and
  `battle.defeated`) remain triggered only through the ordered presentation
  queue. Do not map page navigation or ordinary UI actions to battle sound IDs.

### 3. Accessibility and visual behaviour

- Sound is supplementary only. Keep all existing labels, focus indicators,
  tooltips, visual state, native control semantics, keyboard operation, and
  error/confirmation text unchanged.
- Do not change visual design, screen flow, stage availability, save/progression
  logic, battle rules, route behavior, or backend/API contracts merely to add
  feedback.
- Keep the current restrained pre-alpha volume and cooldown character. Do not
  implement background music, sound settings, volume controls, new production
  files, ambient sound, voice-over, or scene-specific sound designs in this
  task.

### 4. Documentation and tests

- Update the Web UI architecture document to explain the shared UI audio
  boundary, eligible-control convention, and the separate ordered battle-event
  audio boundary. Update the Style Guide with the all-scene interaction rules
  and anti-spam/accessibility guidance.
- Add focused automated tests for every route family above. Verify eligible
  controls unlock/play through the shared path, disabled/decorative controls do
  not play, hover/focus is deduplicated, keyboard Enter/Space yields one click
  cue, and normal navigation/actions still happen.
- Retain AUDIO-001 manager, battle event queue, interaction, target-selection,
  save, stage, Team Builder, Arena, Debug, and Asset Registry regressions.
- Record exact scenes/controls integrated, implementation files, validation,
  reviewer findings, and any skipped control with reason in `Completed.md`.

## Out of Scope

- Any backend, adapter, engine, event schema/order, combat, save/progression,
  stage availability, routing, or API change.
- New sounds, sound redesign, music, global settings/volume controls, audio
  assets, voice, ambient audio, or per-skill/per-scene bespoke sounds.
- Marking a static/decorative/inactive item interactive just to give it sound.
- Modifying owner-controlled `docs/web-ui/screenshots_debug/UI_Review_Human.md`.

## Relevant Files

- `web-ui/lib/audio/AudioManager.ts` and `soundDefinitions.ts` — existing sole
  audio playback/configuration boundary; preserve it.
- `web-ui/lib/audio/battleAudio.ts` — separate the reusable UI interaction
  scope from battle-specific event mapping where appropriate; preserve event
  semantics and no-duplicate guarantees.
- `web-ui/app/layout.tsx` and/or a new small client-only shared UI audio
  boundary — evaluate the safest common integration root without SSR/browser
  misuse.
- `web-ui/components/startup/StartupScreen.tsx` — startup/save-dialog controls.
- `web-ui/components/stages/StageSelectionScreen.tsx` — routes and enabled
  stage hotspots only.
- `web-ui/components/battle/TeamBuilder.tsx`, `BattleExperience.tsx`,
  `ArenaRunExperience.tsx`, `DebugBattleExperience.tsx`, `BattleScreen.tsx`,
  and `web-ui/app/assets/page.tsx` — current player-facing controls.
- Existing audio tests plus route-specific frontend suites under `web-ui/tests/`;
  add focused shared-boundary/route coverage only where needed.
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`, `docs/web-ui/Style_Guide.md`, and
  `docs/Codex/Completed.md` — stable guidance and evidence.

## Acceptance Criteria

1. All current player-facing route families use one centralized UI feedback
   integration and eligible controls provide the existing click/hover cues.
2. jsfxr remains isolated inside `web-ui/lib/audio/`; no component creates a
   competing manager or preset configuration.
3. Battle Screen retains exactly one UI cue per interaction and its battle
   semantic sounds remain ordered/once-only through `usePresentationQueue`.
4. Disabled, static, decorative, inactive, or noninteractive elements remain
   silent; typing, scrolling, pointer movement, and focus changes do not spam.
5. Pointer, keyboard, and touch activation are safe; Enter/Space produces one
   click cue, and browser autoplay/unsupported audio never blocks an action.
6. Existing UI behavior, routes, game mechanics, contracts, and visual/accessibility
   treatment are unchanged except for additive sound feedback.
7. Relevant automated tests, typecheck, lint, production build, and diff check
   pass. Completion records exact coverage and honest manual-test limitations.

## Validation Required

- Add shared-boundary unit/integration tests proving singleton reuse, lazy
  browser unlock, pointer/focus/click/keyboard behavior, no keyboard double
  cue, and disabled/decorative silence.
- Test Startup, Stage Map, Team Builder, Arena Run, Battle, Debug, and Asset
  Registry route families with their available controls. Assert a sound cue is
  requested without requiring an audio device and that the original action
  still completes.
- Re-run AUDIO-001 manager, event-mapping, queue-boundary, and Battle Screen
  tests to prove battle sounds are not duplicated or moved to snapshots/logs.
- Run affected existing save, stage, Team Builder, Arena, Battle, Debug, and
  Asset Registry suites, then `npm run typecheck`, `npm run lint`, production
  build, and `git diff --check`.
- Manually click through each available route after a normal user interaction.
  Confirm feedback is audible but restrained, no initial autoplay occurs, and
  there is no repeated sound. Record unavailable/development-only route limits.

## Agent Assignments

**Complexity/risk assessment:** Medium. The work remains frontend-only but
crosses all interactive route families, SSR/client boundaries, delegated event
handling, navigation/overlay behavior, and existing battle audio deduplication.

**Selected roles — dispatch before implementation:**

- **project-manager:** own cross-route inventory, scope control, phased
  dispatch, owner-file protection, documentation, and completion evidence.
- **ui-developer:** own reusable UI-feedback integration, control marking,
  route integration, SSR/accessibility behavior, and frontend documentation.
- **test-automator:** own deterministic cross-route interaction/deduplication
  coverage, non-blocking action regressions, and validation evidence.
- **reviewer:** independently assess all-scene coverage, duplicate cue risk,
  direct-jsfxr isolation, browser safety, accessibility, and scope compliance.

**Not selected:**

- **game-engine-developer:** deliberately omitted: the task must use the
  existing frontend audio service and published UI events without changing
  engine, adapter, API, game state, or event contracts. Escalate rather than
  expanding scope if an engine change appears necessary.

## Completion Notes

Completed 2026-09-14. AUDIO-002 adds one application-root UI feedback boundary
using the existing AUDIO-001 singleton and `ui.click` / `ui.hover` IDs across
all current player-facing route families. Battle semantic sounds remain
exclusively ordered-presentation-queue feedback. The game-engine-developer was
intentionally omitted because no engine, adapter, API, game-state, or event
contract change was required or made. The owner-controlled
`docs/web-ui/screenshots_debug/UI_Review_Human.md` was preserved without an
AUDIO-002 edit. Exact control coverage, validation, role contributions,
reviewer approval, and manual-device limitations are in `docs/Codex/Completed.md`.
