# Web UI architecture

Stage 1.5/2 is a Next.js presentation client under `web-ui/` connected to the
thin Python adapter. Python remains the sole gameplay authority.

## Boundaries

- `lib/battle/types.ts` mirrors the frozen v1 serializable contract.
- `lib/battle/liveProvider.ts` is the only HTTP-aware frontend module. It owns
  v1 envelope checks, session creation, command transport, and normalized
  rejection/network errors.
- `lib/battle/fixture.ts` owns stateful scripted fixtures; they are presentation
  outcomes, not TypeScript battle rules.
- `lib/battle/formations.ts` is the single duel/duo/trio slot registry. Format
  is derived from snapshot team size, and explicit front/centre/rear positions
  prevent component-level team-size branching.
- `lib/battle/usePresentationQueue.ts` orders semantic events, applies supplied
  post-event values during playback, and replaces visible state with the final
  snapshot. A generation token makes skip/replay race-safe.
- `lib/battle/assets.ts` owns definition-ID presentation and fallback metadata.
- `components/battle/BattleExperience.tsx` is the isolated development shell.
  It selects live 1v1 by default and reads mock/format query controls.
- `components/battle/BattleScreen.tsx` and its child components are generic.
  They contain no API, hero-name, damage, healing, legality, cooldown, status
  duration, turn, summon, or victory rules.

## Authority and reconciliation

Commands carry the expected revision, actor, skill, and selected target IDs.
Only provider `legalActions` enables skills and targets. Local skill/target
selection is allowed; HP, statuses, cooldowns, turns, defeat, and outcomes are
never optimistic.

During playback, only explicit event post-values are shown. The supplied final
snapshot then replaces visible state. Rejected and stale commands reconcile a
returned authoritative snapshot and show distinct feedback. Loading,
disconnected, and adapter-error states expose a retry boundary.

## Assets and accessibility

Ragnar and Nighthawk have stable definition-ID keyed placeholder-ready
portrait, figure, thumbnail, class, active, defeated, and future-animation
metadata. Missing assets use class, generic, then initials fallbacks. `/assets`
shows stable ID, category, resolved path, fallback tier, placeholder/final
status, and association.

Icon controls have accessible names, tooltips are keyboard reachable, focus is
visible, and effects honor reduced motion. Effects use semantic event hints and
presentation metadata and never determine outcomes.

## Runtime caveat

The browser adapter defaults to `http://localhost:8000`; override it with
`NEXT_PUBLIC_BATTLE_API_URL`. A separately hosted frontend requires adapter
CORS configuration or a same-origin proxy. The process-local Python registry
has no persistence or multi-worker consistency, so this milestone uses one API
worker.
