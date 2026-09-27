# UI-027 Pre-Implementation Route, Content, Data, and Risk Audit

**Date:** 2026-09-21  
**Task:** UI-027 — Game Manual, Hero Gallery, Battle Instruction, and Sound Preference  
**Role:** Project manager  
**Status:** Pre-code gate complete; implementation may begin after the API shape below is agreed between engine and UI owners.

## Scope and ownership

UI-027 is a high-risk cross-system task. All five roles in
`docs/Codex/Agent_Roles.md` are selected, as already recorded in
`docs/Codex/Current_Task.md`:

- project manager — this audit, sequencing, scope, documentation, and closure;
- UI developer — routes, Manual dialog, Gallery/Instruction presentation,
  accessibility, assets, and the audio-preference frontend integration;
- game-engine developer — authoritative roster/range/skill/unlock facts and only
  the smallest additive API contract required by the Gallery;
- test automator — deterministic modal, route, data, audio, accessibility, and
  regression coverage; and
- reviewer — independent content-truth, contract, accessibility, scope, and
  evidence review.

The owner-controlled
`docs/web-ui/screenshots_debug/UI_Review_Human.md` was used only as read-only
source evidence. It was already modified in the working tree when this audit
began; UI-027 agents must not edit, reformat, rename, replace, delete, or claim
ownership of that file. The other existing dirty battle-transparency and owner
artwork changes are outside UI-027 and must be preserved.

## Current boundary findings

### Stage Map and routes

- `/stages` is a server page rendering the client
  `StageSelectionScreen`. The current Manual trigger is a disabled native
  button with a gear icon in the upper-right Stage Map navigation. Engineering
  Test & Debugging is a separate bottom-right link. Stage hotspots live in the
  intrinsic map canvas and must remain untouched.
- The repository has no Manual, Hero Gallery, or Battle Instruction route.
  Current routes are `/`, `/stages`, `/game`, `/debug`, and `/assets`.
- `StartupScreen` already supplies a suitable local pattern for a semantic
  modal: `role="dialog"`, `aria-modal`, first-control focus, Escape handling,
  Tab containment, and `requestAnimationFrame` focus restoration.
- The global `body` uses `overflow: hidden`. Dedicated Manual content routes
  therefore need their own height-bounded, vertically scrollable shell; long
  Gallery and Instruction content cannot rely on document-body scrolling.

### Proposed route and focus contract

- Keep the compact menu inside `StageSelectionScreen`; it contains exactly:
  **Hero Gallery**, **Battle Instruction**, and **Sound On/Off**, in that order.
  The close control is outside the menu list.
- Use dedicated routes `/manual/heroes` and `/manual/battle-instruction`.
- Links from either page return to `/stages?manual=open`. The Stage page passes
  this query state into `StageSelectionScreen`, which opens the dialog and
  focuses its first menu option. Closing the dialog by Escape or its close
  control focuses the Manual trigger. This gives a deterministic direct-load
  and client-navigation return path without relying on browser history.
- Closing a locally opened dialog should not navigate. If opened from the
  query marker, closing may replace the URL with `/stages` to avoid a refresh
  unexpectedly reopening it; this must not disturb `debugHotspots=1` during
  development.

### Authoritative roster, ownership, and unlock facts

- `GET /api/v1/heroes` returns exactly ten stable definitions, but only
  `definitionId`, `displayName`, `faculty`, and `specialization`.
- `GET /api/v1/progression` is the authority for the active save slot's
  `unlockedHeroDefinitionIds`. Gallery routes must never persist or infer
  ownership locally. A direct Gallery visit with no active slot must still show
  the ten static definitions but label ownership as unavailable, not falsely
  locked or unlocked.
- New slots own exactly Mage Comprehensiveness, Priest Comprehensiveness,
  Warrior Weapon Master, and Rogue Comprehensiveness.
- Real unlock rewards are:
  - Paladin Protection — Paladin's Altar battle 3;
  - Paladin Retribution — Paladin's Altar battle 6;
  - Paladin Holy — Paladin's Altar battle 9;
  - Warrior Berserker — Warrior's Barrack battle 3; and
  - Warrior Defence — Warrior's Barrack battle 9.
- Priest Discipline is in the approved roster but has no current reward or
  unlock route. The Gallery must explicitly avoid implying one.

### Hero data and content sources

- Engine generation loads HP, Damage, Defence, Agility, magic-resistance
  compensation, and fire/frost/arcane/shadow/death/poison/nature resistance
  intervals from `data/Hero_basic_property.xlsx` and
  `data/Hero_resistance.xlsx`. The generator correlates values and randomizes
  within those inputs. React must describe them as starting-generation ranges,
  not fixed specialization stats or a guaranteed battle roll.
- The current roster response does not publish those ranges, active skill
  inventory, passive classification, or unlock-route metadata. These are game
  facts, not presentation copy, and must not be duplicated in React.
- The smallest coherent contract is an additive extension of each
  `/api/v1/heroes` definition with:
  1. generation ranges for HP, Damage, Defence, Agility, and all seven
     resistance schools;
  2. stable skill identity, display name, and `isPassive` classification; and
  3. a real unlock source (`starter`, a stage/battle reward, or `null`).
  Existing four-field consumers remain compatible if the response model and
  validator accept the additive fields. If the team instead creates a separate
  Gallery endpoint, it must derive from the same engine/progression constants
  and must not instantiate random heroes or advance global RNG merely to answer
  a read request.
- Introductions, brief battle-style summaries, and plain-language skill copy
  belong in a frontend presentation registry keyed by stable definition ID and
  stable skill ID. They must be tested against the authoritative inventory.
  Role labels such as tank/healer/damage are interpretation, not engine
  metadata, so wording must remain descriptive rather than claim a formal role
  rule.
- The only approved passive currently registered is Paladin Protection's Holy
  Aura. Every other profile must render a deliberate passive `N/A` section.
- A current factual drift exists in `web-ui/lib/battle/assets.ts`: its Holy Aura
  status copy says 10–14 HP, while engine behavior and `Combat_System.md` say an
  independently rolled 6–8 HP per living recipient. UI-027 should correct that
  presentation copy; no owner decision is needed because engine and GDD agree.

### Assets and fallback

- `heroPresentation` contains all ten stable definition IDs. Every registered
  portrait path currently exists. Source aspect ratios are not uniform, so the
  Gallery must use `object-fit: cover` for cards and a deliberate profile crop.
- `AssetImage` already resolves requested artwork through registered, class,
  generic, then initials fallback and handles load failure without a broken
  image. Reuse it rather than introducing a parallel image path.
- New artwork is out of scope. The current dirty Paladin Holy artwork and
  backups are owner work and must be preserved.

### Central sound preference

- `UiAudioBoundary` wraps the entire application in `app/layout.tsx` and
  delegates UI click/hover cues to the singleton `audioManager`.
- Ordered battle sounds also call the same singleton through the presentation
  queue. Therefore one enabled/muted gate inside `AudioManager` can silence
  both systems without changing event order or introducing a second playback
  path.
- There is currently no sound preference or browser-storage abstraction.
  Add an SSR-safe, default-on preference at the central manager boundary with a
  small observable API so the Manual state remains current. Read storage only
  in the browser after mount; storage errors and unavailable audio remain
  silent and non-blocking. `unlock()` must still occur only from trusted user
  interaction. The preference is local-device UI state, never save-slot data.

## Screen states

- Manual dialog: closed/open, focus-contained, Escape/close restoration, exact
  ordered menu, current sound state.
- Gallery: roster loading; roster error with retry; progression loading/error
  independent of roster; ten-card ready state; defensive empty state; faculty
  filter with an empty-result message; profile selected/not selected; long
  profile content; and final/fallback artwork.
- Instruction: static, readable heading hierarchy; narrow viewport scrolling;
  clear distinction between engine rules and labelled practical suggestions.
- Gallery ownership must use three states: owned, locked, or unavailable. Do
  not collapse progression failure/no active slot into locked.

## Safe implementation sequence and decision gates

1. **Contract gate — engine owner.** Define and test the additive hero catalogue
   facts from the existing spreadsheets, skill registrations, and progression
   reward constants. Gate passes only when all ten definitions, every current
   skill, the sole passive, seven resistance schools, five real rewards, four
   starters, and Priest Discipline's `null` route are deterministic and no
   request mutates RNG or progression.
2. **Parallel presentation preparation — UI owner.** Create the typed content
   registry and route shells against the agreed contract; author copy only from
   current GDD/engine behavior. Do not hard-code ownership, ranges, or unlock
   rules.
3. **Manual/focus integration — UI owner.** Enable the existing trigger and add
   the dialog/query-return protocol without changing hotspot geometry or debug
   navigation.
4. **Central sound integration — UI owner.** Add one manager-level preference,
   SSR-safe restoration, and subscription. Gate passes only when both delegated
   UI and queue-owned battle sounds are silent while off, then resume without
   replay or event reordering.
5. **Integrated tests — test owner.** Cover contract drift, all ten definitions,
   modal order/focus/Escape, routes/return, independent data failures, filters,
   passive `N/A`, assets/fallbacks, ownership/unlock truth, storage failure,
   autoplay safety, sound suppression/re-enable, and unchanged Stage Map/audio
   behavior.
6. **Manual validation and documentation — PM/UI/test.** Validate desktop and
   narrow/touch-like layouts, long content, keyboard flow, locked/unlocked and
   unavailable ownership, and sound across a UI control plus a battle event.
   Update API/data contract, architecture, Screen Flow, Style Guide, Hero/Skill
   documentation only where stable truth changed, then obtain independent
   reviewer approval before completion.

The critical path is contract agreement -> typed UI consumption -> integrated
tests -> independent review. Modal styling, presentation-copy drafting, and
route shell work may proceed in parallel after field names are agreed.

## Risks, controls, and escalation triggers

| Risk | Control | Escalate when |
|---|---|---|
| React copies or derives engine ranges/skills/unlocks | Additive engine-owned catalogue fields and drift tests | The engine cannot expose a fact without random hero construction or duplicated untestable metadata |
| Misleading fixed-stat presentation | Label all values as correlated randomized starting ranges | Requested copy promises a particular battle roll |
| False Priest Discipline route | Authoritative `null` unlock source and explicit test | Any current reward is discovered outside `STAGE_BATTLES` |
| Modal breaks map hotspots or focus | Keep overlay/navigation outside map canvas; reuse proven focus trap pattern | Manual interaction changes hotspot geometry or focus cannot reliably return |
| Direct route has no active slot | Render roster and ownership-unavailable state | Product requires Gallery access to be blocked instead |
| Sound preference duplicates playback or bypasses autoplay | Gate the existing singleton only; no new provider | A proposed implementation hooks snapshots/log rendering or calls provider directly |
| Storage causes hydration/runtime failure | Browser-only restoration, default on, caught failures | Preference must synchronize across devices/save slots (out of scope) |
| Long content is clipped by global body overflow | Route-local scroll region with stable gutter | Narrow/touch-like manual validation cannot reach all content |
| Content claims unsupported formal roles/formulas | Presentation-only language and independent factual review | A desired statement is not supported by engine/GDD truth |
| Dirty owner/parallel changes are overwritten | Limit edits to named UI-027 files; review the final diff by ownership | An implementation requires touching owner artwork or `UI_Review_Human.md` |

## Implicated files and contracts

- UI/routes: `web-ui/components/stages/StageSelectionScreen.tsx`,
  `web-ui/app/stages/page.tsx`, new `web-ui/app/manual/...` pages and Manual
  components, `web-ui/app/globals.css`.
- Data/API: `battle_api/adapter.py`, `battle_api/models.py`, optionally
  `battle_api/app.py`; `web-ui/lib/battle/types.ts` and `liveProvider.ts`.
- Presentation/assets: `web-ui/lib/battle/assets.ts`,
  `web-ui/components/battle/AssetImage.tsx`, and a new stable-ID content
  registry.
- Audio/storage: `web-ui/lib/audio/AudioManager.ts`,
  `web-ui/components/audio/UiAudioBoundary.tsx`, and focused audio tests.
- Existing regression suites: `ui-012-stage-selection`,
  `ui-017-stage-and-structured-config`, `ui-023-arena-debug`, roster/provider,
  progression, `audio-manager`, `ui-audio-boundary`, `battle-audio`, and
  presentation-queue audio tests; add a focused UI-027 suite and backend
  catalogue contract tests.
- Documentation on completion: `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`,
  `PYTHON_ADAPTER_API.md`, `WEB_UI_ARCHITECTURE.md`, `Screen_Flow.md`,
  `Style_Guide.md`, relevant GDD/Technical truth only if changed,
  `docs/Codex/Current_Task.md`, and `docs/Codex/Completed.md`.

## Audit outcome

No owner decision blocks implementation. The material gap is engineering-owned:
the current roster contract is too small for truthful Gallery ranges,
skill/passive inventory, and unlock-source presentation. Close that gap through
one additive, deterministic, non-mutating contract before wiring final Gallery
content. Preserve Priest Discipline's absent unlock route and correct the stale
Holy Aura 10–14 presentation copy to the authoritative 6–8 value.

## 2026-09-22 Approved Concept Mapping

The owner-supplied `Hero_Gallery_Concept.png` is a read-only visual target,
not a source of gameplay values, identities, roles, or artwork. Its fictional
Holy Knight profile and numbers are not copied. The implementation maps the
concept to the authoritative UI-027 architecture as follows:

| Concept element | UI-027 implementation rule |
| --- | --- |
| Isolated atmospheric header | The Gallery header contains only **Back to Manual**; a route-local cinematic dark navy/black background sits behind the compendium surface. |
| Two-region desktop compendium | A left browsing panel holds the title, ordered filters, cards, and lower-left quotation/breathing space. A right profile panel holds identity, battle style, Base Range properties, and skills. |
| Large centre hero art | `AssetImage` uses the selected definition's registered figure with aspect-preserving containment, a lower fade, and initials/class fallback; no source art is changed or recropped in files. |
| Gold frames and selected illumination | Fine gold rules/corner ornamentation and a restrained selected-card halo replace generic rounded dashboard cards. Ownership remains textual as well as coloured. |
| Property block | Engine-owned configured ranges render as **PROPERTIES (Base Range)**: HP/Damage, Defence/Agility, then all seven resistance schools. The existing randomized-range explanation remains adjacent. |
| Active/Passive skill section | Actual `isPassive` skill data determines accessible tabs and counts. Stable skill IDs select registry copy; accordion rows preserve `aria-expanded`. A zero-passive definition displays a professional N/A panel. |
| Responsive order | Desktop keeps two regions. Tablet retains filters/cards and moves profile art without clipping. Mobile reads title, filters, cards, selected art, identity/introduction, Battle Style, Base Range properties, tabs, then accordions; no horizontal overflow is permitted. |

Additional concept validation must cover desktop composition/cropping/text
overlap, long profile content, locked state, keyboard tabs/accordions, and
tablet/mobile horizontal overflow. The Gallery currently has no factual data
gap: backend catalogue data is additive/read-only, ownership remains active-slot
progression-only, and Priest Discipline remains an explicit no-route profile.
