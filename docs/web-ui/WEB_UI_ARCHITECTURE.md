# Web UI architecture

Stage 1 is a presentation-only Next.js client under `web-ui/`. Python remains
the sole gameplay authority.

## Boundaries

- `lib/battle/types.ts` mirrors the versioned data contract as strict,
  serializable TypeScript types.
- `lib/battle/fixture.ts` is the isolated, stateful mock-provider
  implementation. It owns scripted fixture outcomes, preserves earlier
  commands/demos, and returns complete reconciled snapshots.
- `lib/battle/usePresentationQueue.ts` orders semantic events, applies supplied
  post-event values for visual playback, and replaces visible state with the
  provider's final snapshot after each script. A per-run generation invalidates
  stale continuations; skip is enabled only after the final snapshot is
  available and reconciles it atomically.
- `lib/battle/assets.ts` is the single asset and effect-presentation registry.
  Missing hero art falls back to clearly labelled original CSS placeholders.
- `components/battle/` contains visual components. Components calculate bar
  percentages and control presentation preferences only; they contain no
  damage, healing, legality, cooldown, duration, turn, summon, or victory rules.

## Integration seam

A live adapter implements injected `BattleProvider.getState()` and
`submitCommand(command)`. Commands carry `expectedRevision`, actor, skill, and
selected target IDs. The provider supplies snapshots, `legalActions`, ordered
semantic events, and final reconciled snapshots. No
component changes or fixture-name checks are required. Input remains blocked
during required playback, while speed, skip, fullscreen, cleared log, selected
controls, and auto-battle are explicitly local presentation preferences.

## Assets and accessibility

Repository-owned class icons are copied into `public/game-assets/classes`.
Hero art, skill art, and effects are original CSS/typographic placeholders and
are marked as such on `/assets`. Icon-only controls have names, status tooltips
are keyboard accessible, interactive controls have visible focus states, and
motion is minimized for `prefers-reduced-motion`.
