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
- `lib/battle/formations.ts` is the single duel/duo/trio slot registry. Format
  is derived from authoritative team size.
- `lib/battle/usePresentationQueue.ts` orders semantic events, applies supplied
  post-event values, and reconciles to the final snapshot. Typed semantic
  events always drive playback and state; additive `battleLog` events carry
  Python-authored display prose. A generation token makes skip/replay
  race-safe.
- `lib/battle/assets.ts` owns definition/status presentation and fallback
  metadata.
- `lib/battle/battleBackgrounds.ts` owns the fixed BG03 battle-scene background
  constant used by presentation only.
- `components/battle/BattleExperience.tsx` owns the Team Builder/battle
  lifecycle. It loads the authoritative roster, creates a fresh provider for
  each configuration, and unmounts the battle subtree on return.
- `components/battle/TeamBuilder.tsx` owns local pre-battle selection and
  validation only. It contains no hero construction, random composition,
  combat, AI, or targeting rules.
- `components/battle/BattleScreen.tsx` and its child components are generic.
  They contain no API, hero-name, damage, healing, legality, cooldown, status
  duration, turn, summon, or victory rules.

## Authority and Reconciliation

Team Builder sends battle size, ordered teams, enemy composition mode, enemy
control mode, and optional seed. The adapter validates and constructs the
engine session. Random enemy selection and all computer turns happen in Python.

Commands carry the expected revision, actor, skill, and selected target IDs.
The explicit provider `turnControl` boundary must accept commands before the UI
enables interaction; `legalActions` then enables exact skills and targets.
React never interprets Stun, Scoff, or another status to decide command
ownership. Local selection is allowed; HP, statuses, cooldowns, turns, defeat,
and outcomes are never optimistic.

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

`BattleCreateConfiguration` contains `battleSize`, `playerTeam`,
`enemyCompositionMode`, optional `enemyTeam`, `enemyControlMode`, and optional
`seed`. The roster is loaded from `GET /api/v1/heroes`; the client rejects
wrong-version or malformed roster responses.

Returning from an ended battle discards the provider and keyed battle
component. This clears the battle ID, cached snapshot/revision, presentation
generation, timers, log, selections, and modal state. Relaunch sends a new
`POST /api/v1/battles` and uses the fixed BG03 cosmetic battle background. It
is not connected to the engine seed or battle data contract.

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

Current final figure registrations cover Paladin Protection, Paladin
Retribution, Priest Comprehensiveness, Priest Discipline, Warrior Defence, and
Warrior Weapon Master, Mage Comprehensiveness, and Rogue Comprehensiveness.

Battle-session display names come from the adapter and are presentation data;
stable definition and combatant IDs remain the only identity keys. Side cards
show faculty and specialization together, while summons retain their explicit
summon label.

Icon controls have accessible names, status tooltips are pointer/keyboard
reachable, and focus is visible. Team Builder uses native radio, select, and
input controls. The battle-completion dialog moves and contains focus on its
Return action. Effects honor reduced motion and never determine outcomes.

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

`lib/battle/assets.ts` owns `heroFigureScales`, a centralized, stable
definition-ID registry for battlefield-only visual tuning. Each supported
definition defaults to `1.0`; the value multiplies its formation scale without
changing portraits, team cards, engine state, or API payloads. Unknown IDs use
the neutral default.

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
