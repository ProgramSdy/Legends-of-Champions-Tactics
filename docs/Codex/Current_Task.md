# Current Task

**Status:** Ready for Core Team

**Task:** UI-027 — Game Manual, Hero Gallery, Battle Instruction, and Sound Preference

**Owner request date:** 2026-09-21

**Source review:** `docs/web-ui/screenshots_debug/UI_Review_Human.md` —
2026-09-21 entry (owner-controlled; read only).

## Objective

Turn the existing disabled **Manual** control on the Stage Map into a compact,
accessible Game Manual. Its menu must contain exactly these three options, in
this order:

1. Hero Gallery
2. Battle Instruction
3. Sound On/Off

Implement a responsive dark-fantasy Hero Gallery and a readable Battle
Instruction guide, plus a global locally persisted sound preference that
controls both UI and battle sound effects through the existing central audio
system.

## Background

`StageSelectionScreen` already contains the disabled Manual button. The
authoritative `GET /api/v1/heroes` roster provides the ten approved stable
definition IDs and identity data; `GET /api/v1/progression` provides the active
save slot's unlocked definition IDs. The existing asset registry and
`AssetImage` component provide final/fallback hero artwork. The audio singleton
is `web-ui/lib/audio/AudioManager.ts`; UI sound is delegated at the application
boundary and battle-event sound is queue-owned.

Hero starting attributes are deliberately randomized within engine-authorized
ranges. The Gallery must explain this clearly: displayed range information is
not a permanent per-specialization stat sheet or a promise of a specific battle
roll. Python remains authoritative for all live combat and progression state.

## First Milestone — Plan and Audit Before Editing

Before implementation, the project manager must record a short dated plan in
`docs/Codex/Analysis/` that states:

- proposed Manual-dialog and Gallery/Instruction routes, including a reliable
  return path to Stage Map and focus restoration to Manual;
- page/component structure and loading/error/empty states;
- the content-source design: a maintainable presentation-content registry
  keyed by stable definition ID, and which range/skill/ownership facts require
  an authoritative backend contract rather than React-owned logic;
- current roster, progression, reward/unlock-route, asset/fallback, audio, and
  browser-storage findings; and
- any material data gap or rule ambiguity requiring escalation before it is
  presented to players.

Then implement the approved plan. Do not pause for a trivial implementation
choice; escalate only if a genuine owner decision or missing game truth blocks
an accurate result.

## Requirements

### Game Manual window

- Enable the Stage Map Manual button. It opens a compact dark-fantasy modal or
  dialog with exactly the three menu options listed in the Objective, in that
  order. A close control is permitted but is not a fourth menu option.
- It must support mouse, touch, and keyboard activation; trap/manage focus
  correctly, close by Escape and close control, and return focus to the Manual
  trigger. Opening/closing and menu actions must retain existing UI-audio
  behaviour subject to the user's sound preference.
- Do not disturb existing Stage Map hotspots, title/debug navigation, map
  coordinate geometry, progression, or route behaviour.

### Hero Gallery

- Provide a dedicated, accessible Gallery route/page reachable from Manual and
  a clear route back to Stage Map/Manual.
- Show exactly the ten approved web specializations from `Hero_System.md`, with
  faculty filtering and illustrated cards. Use stable definition IDs for
  identity and the existing asset resolver/fallback; never show a broken image.
- Selecting a hero opens a profile containing: large artwork; faculty and
  specialization; a brief introduction; a plain-language battle-style summary;
  explained ranges for HP, Damage, Defence, Agility, and every currently
  supported magic-resistance school; expandable active-skill descriptions; and
  a clearly separate passive section. Where no passive is designed, show a
  professional `N/A` state rather than hiding the section.
- Keep introductions and player-facing skill copy in a maintainable
  presentation-content registry. Every factual claim must be checked against
  current hero/skill/Combat documentation and live engine behaviour.
- Read ownership only from the active save slot's authoritative backend data.
  Locked heroes remain fully viewable. Show an unlock route only when a real
  current route/reward exists. In particular, do not imply that Priest
  Discipline currently has an unlock route.
- Do not display battle-specific preview numbers as permanent skill values and
  do not calculate damage, healing, hit chance, target legality, or status
  outcomes in React.

### Battle Instruction

- Provide a dedicated, readable guide reachable from Manual with a clear return
  to Stage Map/Manual.
- Cover player-facing battle basics, skill and target selection, turn flow,
  victory conditions, 2v2/3v3 formations, front/rear targeting, statuses, and
  a small set of clearly labelled practical strategy tips.
- Check every rules statement against the current engine and project
  documentation. Explain mechanics plainly without exposing implementation
  details, treating suggestions as engine rules, or inventing universal combat
  formulas.

### Sound On/Off

- Implement this only as the third Manual menu control, not a separate page.
  Clearly show its current state.
- Connect it to the existing central `AudioManager` so it silences/enables both
  delegated UI feedback and queue-owned battle-event sound. It must not bypass
  browser autoplay/trusted-interaction restrictions, reorder events, or create
  a parallel playback path.
- Persist the preference locally only when the current architecture supports it
  safely (SSR-safe storage access and a sensible default). It is not save-slot,
  progression, or gameplay state. Graceful storage/audio unavailability must
  stay non-blocking and silent.

### Quality and preservation

- Maintain the established dark-fantasy visual language, responsive layout,
  readable long content, visible focus, semantic headings/labels, and reduced
  motion support where relevant.
- Preserve Startup, Stage Map, Team Builder, Arena, Battle, Debug, Asset
  Registry, audio event ordering, save-slot behaviour, backend/API contracts,
  and all existing working functionality except enabling/replacing the Manual
  placeholder as specified.

## Out of Scope

- New hero classes/specializations, unlock rewards/routes, progression rules,
  player account/cloud saves, levelling/equipment/rarity, changed battle
  mechanics/balance, client combat simulation, generic hero-wiki tooling,
  new hero artwork, background music, or a wholesale Stage Map redesign.
- A false Priest Discipline unlock route; hidden locked heroes; raw formula or
  Battle Information Transparency detail; arbitrary status serialization; and
  a save-slot-backed audio preference.

## Relevant Files

- `web-ui/components/stages/StageSelectionScreen.tsx`, `web-ui/app/stages/`,
  route layout files, `web-ui/app/globals.css`, and Stage Map tests.
- `web-ui/lib/battle/liveProvider.ts`, `types.ts`, `assets.ts`, and
  `web-ui/components/battle/AssetImage.tsx` — roster, progression, assets, and
  fallback presentation.
- `web-ui/lib/audio/AudioManager.ts`, `soundDefinitions.ts`, `uiAudio.ts`,
  `web-ui/components/audio/UiAudioBoundary.tsx`, battle audio/queue files, and
  audio tests.
- `battle_api/adapter.py`, `battle_api/app.py`, `battle_api/models.py`, and
  `battle_api/progression.py` if a minimal additive authoritative Gallery-data
  contract is genuinely needed.
- `docs/GDD/Hero_System.md`, `Skill_System.md`, `Combat_System.md`,
  `Game_Design_Document.md`; `docs/Technical/Architecture.md`,
  `Player_Data_and_Save_System.md`; and web UI architecture, contract, screen
  flow, and style documents.

## Acceptance Criteria

1. Stage Map Manual opens an accessible compact dialog with exactly Hero
   Gallery, Battle Instruction, and Sound On/Off, in the required order.
2. The Gallery accurately presents all ten approved definitions, filtering,
   selection, artwork fallback, profile content, randomized-stat explanation,
   visible locked states, and only real unlock routes.
3. Battle Instruction is player-readable and factually aligned with current
   engine/GDD rules, with suggestions clearly distinguished from rules.
4. The sound toggle changes and persistently restores the central UI and battle
   sound preference without weakening autoplay safety or audio ordering.
5. Navigation, focus restoration, Escape, keyboard, touch, responsive layout,
   loading/error states, existing map hotspots, save/progression, and battle
   flow all remain correct.
6. Documentation distinguishes stable gameplay truth from presentation copy,
   reflects new routes/audio preference/data contract if any, and records data
   gaps and limitations honestly.

## Validation Required

- Add focused tests for Manual ordering, modal focus/Escape/return focus,
  navigation, all ten roster cards/faculty filters, selected profile/passive
  `N/A`, final/fallback artwork, active-slot ownership/locked display, real vs
  absent unlock routes, stat randomization copy, and empty/error/long-content
  states.
- Test factual Battle Instruction content against documented rules where
  practical, and prevent unsupported presentation claims from silently
  appearing.
- Test sound default/persistence/storage failure, UI and battle-event silence
  while off, re-enable behaviour, browser unlock safety, duplicate prevention,
  and unchanged event ordering.
- Run relevant backend/API/progression tests if contracts change; focused and
  broader frontend tests; typecheck, lint, production build, Python compile,
  and diff check. Manually validate desktop and narrow/touch-like views across
  navigation, modal focus, Gallery, Instruction, locked/unlocked state, and
  sound preference. Record exact evidence and limitations.

## Agent Assignments

**Complexity/risk:** High. This is a cross-system player-facing navigation,
presentation-content, authoritative-progression, asset, global-audio, storage,
accessibility, testing, and documentation task. All five roles are required.

- **project-manager:** own the first-milestone plan/audit, route/content/data
  decisions, five-role dispatch, scope, documentation, and completion record.
- **ui-developer:** own Manual/Gallery/Instruction routes and components,
  responsive/accessibility/focus handling, content registry, asset fallback,
  and central audio-preference frontend integration.
- **game-engine-developer:** audit truth for hero stats/skills/instructions and
  progression/unlock routes; own only any necessary additive authoritative
  Gallery contract and its compatibility documentation/tests.
- **test-automator:** own deterministic route/modal/roster/ownership/audio
  persistence/accessibility coverage and integrated regression evidence.
- **reviewer:** independently review content truth, scope, progression/audio
  safety, accessibility, contracts, and validation evidence.

## Completion Notes

Pending implementation, validation, and independent review.
