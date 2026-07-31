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
- `lib/battle/battleBackgrounds.ts` owns the explicit battle-scene background
  registry and presentation-only random selection.
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
`POST /api/v1/battles` and selects a fresh cosmetic battle background. The
selected background remains stable for the mounted battle and is not connected
to the engine seed or battle data contract.

## Assets and Accessibility

Approved heroes use stable definition-ID keyed placeholder-ready portrait,
figure, thumbnail, class, active, and defeated metadata. Missing assets use
class, generic, then initials fallbacks. `/assets` exposes asset diagnostics.

Battle-session display names come from the adapter and are presentation data;
stable definition and combatant IDs remain the only identity keys. Side cards
show faculty and specialization together, while summons retain their explicit
summon label.

Icon controls have accessible names, status tooltips are pointer/keyboard
reachable, and focus is visible. Team Builder uses native radio, select, and
input controls. The battle-completion dialog moves and contains focus on its
Return action. Effects honor reduced motion and never determine outcomes.

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
- 2026-07-31 — Added explicit authoritative turn-control gating and transient
  automatic/skip presentation; React does not infer restriction rules.
- 2026-07-31 — Added UI-006 engine-authored battle-log presentation, runtime
  display names independent of stable IDs, full profession labels, and refined
  duel/duo/trio command-deck presentation.
