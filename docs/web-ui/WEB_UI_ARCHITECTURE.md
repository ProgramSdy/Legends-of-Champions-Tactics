# Web UI Architecture

The web client is a Next.js presentation client under `web-ui/` connected to
the thin Python adapter. Python remains the sole gameplay authority.

## Boundaries

- `lib/battle/types.ts` mirrors the v1 serializable battle contract and the
  additive UI-002 creation configuration.
- `lib/battle/liveProvider.ts` is the only HTTP-aware frontend module. It owns
  roster and envelope validation, configurable session creation, command
  transport, and normalized rejection/network errors.
- `lib/battle/fixture.ts` owns stateful scripted fixtures; they are presentation
  outcomes, not TypeScript battle rules.
- `lib/battle/formations.ts` is the single duel/duo/trio coordinate registry.
  Format is derived from authoritative team size; for 2v2 it selects the
  approved coordinate pair from the side's two supplied combatant `position`
  values and uses each supplied ordered `slot`. It never assigns a gameplay
  position.
- `lib/battle/usePresentationQueue.ts` orders semantic events, applies supplied
  post-event values (including additive status stack counts), and reconciles to
  the final snapshot. Typed semantic
  events always drive playback and state; additive `battleLog` events carry
  Python-authored display prose. A generation token makes skip/replay
  race-safe.
- `lib/battle/assets.ts` owns definition/status presentation and fallback
  metadata.
- `lib/battle/battleBackgrounds.ts` owns the fixed BG03 battle-scene background
  constant used by presentation only.
- `components/startup/StartupScreen.tsx` owns the non-interactive cinematic
  title presentation at `/`. It uses the supplied direct public startup and
  logo assets and a semantic link to `/stages`; it contains no battle state,
  roster loading, or adapter logic.
- `components/stages/stage-config.ts` owns presentation-only stage IDs, display
  names, enabled state, and map-percentage geometry. Inactive stage definitions
  omit destinations and geometry so they cannot render as controls before
  approval.
- `components/stages/structured-stage-config.ts` owns reusable frontend-only
  structured-stage data: approved player definition IDs and ordered fixed
  battle definitions. It does not model profile state, unlocks, rewards,
  persistence, or Python gameplay data.
- `components/stages/StageSelectionScreen.tsx` owns the map-bound Arena and
  Warrior's Barrack interactions at `/stages`. Their hotspot, label, glow, and
  optional debug outline share one intrinsic `1672 / 941` positioning parent.
- `components/battle/BattleExperience.tsx` owns the Team Builder/battle
  lifecycle. It loads and preflights the authoritative roster, creates a fresh
  provider for each existing request configuration, and owns the temporary
  structured-stage battle index in client memory.
- `components/battle/TeamBuilder.tsx` owns local pre-battle selection and
  validation only. Arena mode retains its complete roster and editable Battle
  Rules. Structured mode receives data from the stage configuration, filters
  the adapter roster to its allowed player definitions, and renders fixed
  format/enemy data without editable counterpart controls. It contains no hero
  construction, random composition, combat, AI, or targeting rules. Its
  scrollable grid uses content-sized implicit rows so its team panels, Matrix,
  and launch footer remain in normal vertical document flow when viewport
  height is constrained.
- `components/battle/BattleScreen.tsx` and its child components are generic.
  They contain no API, hero-name, damage, healing, legality, cooldown, status
  duration, turn, summon, or victory rules.

## Authority and Reconciliation

Team Builder sends battle size, ordered teams, enemy composition mode, enemy
control mode, and optional seed. A 2v2 request additionally sends the selected
`playerFormation`; it sends `enemyFormation` only for a player-controlled
enemy. For a computer-controlled enemy the field is omitted and the adapter
uses the seeded session random source. The adapter validates the request,
assigns each engine hero's `front`/`rear` position, and constructs the session.
Random enemy selection and all computer turns happen in Python.

Commands carry the expected revision, actor, skill, and selected target IDs.
The explicit provider `turnControl` boundary must accept commands before the UI
enables interaction; `legalActions` then enables exact skills and targets.
React never interprets Stun, Scoff, or another status to decide command
ownership. Local selection is allowed; HP, statuses, cooldowns, turns, defeat,
and outcomes are never optimistic.

The battlefield consumes each snapshot combatant's `position` and `slot` only
for 2v2 presentation placement. Target controls continue to use only the
adapter's `legalActions.validTargetIds`; React does not recreate melee
front/rear legality or position-based damage rules.

During playback, explicit turn events identify the transient acting hero,
restriction reason, status application/removal, and supplied post-values while
all command controls remain disabled. The supplied final snapshot then replaces
visible state. Rejected and stale commands reconcile an authoritative snapshot
and show distinct feedback. Loading, disconnected, and adapter-error states
expose retry boundaries.

The presentation queue processes every typed semantic event even when
`visibleInLog` is false. That flag suppresses only the event's generic log copy
when an ordered, sanitized `battleLog` line from Python already describes it.
The client displays `battleLog` prose but never parses it for state, legality,
identity, or animation decisions.

## Session Lifecycle

The application first opens the cinematic title scene at `/`. Activating its
keyboard-accessible `START GAME` link opens `/stages`; enabled map controls
navigate to `/game?stage=<stageId>`. `GamePage` resolves the enabled stage and
passes its ID to `BattleExperience`; direct or invalid `/game` visits fall back
safely to Arena. This does not alter `BattleCreateConfiguration` or any battle
request. `/assets` remains a development route and returns directly to `/game`,
never through the title screen.

`BattleCreateConfiguration` contains `battleSize`, `playerTeam`,
`enemyCompositionMode`, optional `enemyTeam`, `enemyControlMode`, and optional
`seed`. Its discriminated 2v2 branch requires `playerFormation` and additionally
requires `enemyFormation` when enemy control is `player`; the 1v1/3v3 branches
prohibit both formation fields. The roster is loaded from `GET /api/v1/heroes`;
the client rejects wrong-version or malformed roster responses.

Returning from an ended battle discards the provider and keyed battle
component. This clears the battle ID, cached snapshot/revision, presentation
generation, timers, log, selections, and modal state. Arena then returns to
its local builder. In a structured stage, `BattleScreen` forwards the actual
typed `BattleOutcome` from the authoritative ended snapshot to
`BattleExperience`: friendly victory advances the in-memory index, while
enemy victory, draw, and round limit return to the same preparation state.
The final friendly victory clears the index and routes to `/stages`. Relaunch
sends the same existing `POST /api/v1/battles` request shape and uses the fixed
BG03 cosmetic battle background; no API, profile, save, or persistence state
is introduced.

After the Team Builder enters a battle, the live `BattleScreen` mounts and
creates the session while a centered `3 → 2 → 1 → START` overlay keeps the
fully composed battlefield non-interactive. The background, figures, team
panels, turn chrome, and command deck remain visible. Numeric steps use one
stable metric box; `START` has a deliberately separate label treatment. When
an opening script is present, the UI waits for the overlay to finish, presents
the script from its authoritative pre-resolution snapshot, and only then
allows commands. The queue cancels stale timers and scripts on retry, unmount,
or a new provider.

## Assets and Accessibility

Approved heroes use stable definition-ID keyed placeholder-ready portrait,
figure, thumbnail, class, active, and defeated metadata. Missing assets use
class, generic, then initials fallbacks. `/assets` exposes asset diagnostics.

Final battlefield figures are registered by stable hero definition ID. Public
art under `/game-images/` loads from its direct static URL rather than the
framework image optimizer, while genuine load failures retain the normal
fallback chain. Requested final figure artwork keeps its source orientation on
the friendly side and is horizontally mirrored on the enemy side. Mirroring is
limited to the image pixels; formation movement, target controls, overhead
health/status UI, labels, portraits, and thumbnails are unchanged.

Current final figure registrations cover Paladin Protection, Retribution, and
Holy; Priest Comprehensiveness and Discipline; Warrior Defence, Weapon Master,
and Berserker; Mage Comprehensiveness; and Rogue Comprehensiveness. The Holy
registry uses the canonical public path
`/game-images/heroes/Paladin-Holy/figures/Paladin_Holy.png`; it is the
hash-preserving rename of the owner-supplied Holy artwork.

Battle-session display names come from the adapter and are presentation data;
stable definition and combatant IDs remain the only identity keys. Side cards
show faculty and specialization together, while summons retain their explicit
summon label.

Icon controls have accessible names, status tooltips are pointer/keyboard
reachable, and focus is visible. Team Builder uses native radio and input
controls for Battle Rules, plus native buttons for player slots, specified-enemy
slots, and Hero Selection Matrix assignment. Matrix and slot imagery use
the shared `AssetImage` requested/class/initials fallback chain in a bounded
media frame. The battle-completion dialog moves and contains focus on its
Return action. Effects honor reduced motion and never determine outcomes.

`StatusIcon` is the shared status renderer for both battlefield overhead
HP/status panels and Team Information cards. It displays a supplied valid stack
count in a compact lower-right badge, retaining the exact count in its tooltip
and accessible name. The presentation queue uses an explicit event count when
provided, preserves an existing count for legacy events that omit it, and lets
the final Python snapshot win after playback.

Battle figures use one contained, bottom-aligned, 172px-wide footprint for
direct final artwork and the fallback renderer. A loaded final image reports
its intrinsic dimensions to the figure and establishes its own frame height;
missing or failed images retain a 202px fallback frame. The HP/status panel
uses that frame and the formation scale to preserve a 12px visual clearance.
Each figure owns its centered aura and transient target-bound effects. Healing appears green; an additive adapter
`statusPresentation` value authoritatively selects blue buff or red debuff
rings. The client never classifies a status locally. Attack-lunge direction is
derived from the acting combatant's side while the authoritative formation and
combat positions remain unchanged.

The additive typed `damagePrevented` event is rendered only at its supplied
target as a golden shield and visible zero damage. It is emitted by the adapter
only for the engine-authored Shield of Protection prevention reason; React does
not infer prevention from unchanged HP, a snapshot status, or hero identity.
Status registry expansion is likewise cross-boundary: each adapter-visible
stable status ID requires matching frontend metadata and shared-icon/effect
regression coverage before a new hero is exposed.

`lib/battle/assets.ts` owns `heroFigureScales`, a centralized, stable
definition-ID registry for battlefield-only visual tuning. Values multiply a
hero's formation scale without changing portraits, team cards, engine state, or
API payloads. The present non-neutral values are owner-approved visual tuning;
unknown IDs use the neutral `1.0` default.

The Team Builder and `/assets` registry are finite, keyboard-focusable desktop
scroll regions with a stable scrollbar gutter when their content overflows.
Their mobile layouts retain normal document scrolling.

## Runtime Caveat

The browser adapter defaults to `http://localhost:8001`; override it with
`NEXT_PUBLIC_BATTLE_API_URL`. A separately hosted frontend requires adapter
CORS configuration or a same-origin proxy. The process-local Python registry
has no persistence or multi-worker consistency, so this milestone uses one API
worker.

## Change Log

- 2026-07-29 — Added UI-002 Team Builder, roster discovery, configurable live
  1v1/2v2/3v3 lifecycle, computer-turn boundary, and completion reset.
- 2026-07-30 — Added presentation-only random battle backgrounds selected once
  per newly started battle.
- 2026-08-02 — Retired BG01 and BG02 from live presentation; all battles use
  the fixed BG03 background.
- 2026-07-31 — Added explicit authoritative turn-control gating and transient
  automatic/skip presentation; React does not infer restriction rules.
- 2026-07-31 — Added UI-006 engine-authored battle-log presentation, runtime
  display names independent of stable IDs, full profession labels, and refined
  duel/duo/trio command-deck presentation.
- 2026-08-01 — Registered the Paladin Protection battlefield figure, direct
  `/game-images/` loading, and enemy-only final-figure mirroring.
- 2026-08-01 — Registered final battlefield figures for Paladin Retribution,
  Priest Comprehensiveness, Warrior Defence, and Warrior Weapon Master.
- 2026-08-01 — Normalized the Paladin Protection asset folder and registry URL.
- 2026-08-02 — Added UI-007 shared battlefield figure geometry, target-bound
  effects driven by the adapter's additive status presentation cue, side-aware
  lunges, consistent specified-enemy labels, and bounded Builder/Asset
  Registry scrolling.
- 2026-08-02 — UI-008 replaced the earlier standalone entry countdown with a
  fully composed in-scene overlay and documented the authoritative playable
  opening lifecycle (`openingSnapshot` / `playOpening`).
- 2026-08-03 — Registered supplied final battlefield figures for Mage
  Comprehensiveness and Rogue Comprehensiveness.
- 2026-08-05 — Added the cinematic startup title route at `/`, moved the
  unchanged playable entry to `/game`, and redirected the Asset Registry return
  link to `/game`.
- 2026-08-08 — Added the map-bound `/stages` selector, its single enabled Arena
  control, development-only hotspot debug affordance, and a presentation-only
  six-location configuration.
- 2026-08-09 — UI-013 added the presentation-only Arena query handoff, Current
  Stage preview, Back to Stage Map control, visual player/enemy slots, and the
  Hero Selection Matrix while preserving Battle Rules and the battle-create
  contract.
- 2026-08-09 — UI-014 expanded the live adapter roster to ten definitions and
  refined Team Builder to fixed disabled slots, profession-only identity,
  roster-derived faculty filtering, and bounded Matrix paging.
- 2026-08-10 — UI-016 added the typed engine-authored Shield of Protection
  prevention presentation and completed the adapter/frontend status boundary
  for Paladin Holy and Warrior Berserker's five player-visible statuses.
- 2026-08-10 — UI-017 activated Warrior's Barrack using reusable
  frontend-only structured-stage data, an in-memory outcome-aware three-battle
  lifecycle, and immutable predefined battle teams.
- 2026-08-14 — UI-018 added the typed 2v2 formation request handoff,
  snapshot-position-driven duo placement, player-selectable formation controls,
  computer-enemy formation explanation, and `validTargetIds`-only target
  presentation. Duel and trio placement remain unchanged.
