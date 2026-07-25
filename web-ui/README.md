# Legends of Champions Tactics — Web UI

Stage 1 is a presentation-only battle-screen vertical slice. The Python engine
remains authoritative for rules and outcomes.

## Run and validate

Requires Node.js 22.13 or newer.

```bash
npm install
npm run dev
npx tsc --noEmit --incremental false
npm run lint
npm run build
```

Open `/` for the battle and `/assets` for the asset/fallback gallery.

## Component and data shape

- `components/battle/BattleScreen.tsx` is the provider-injected generic screen.
- `components/battle/MockBattleScreen.tsx` adds fixture-only demo controls.
- `components/battle/` contains hero, skill, status, meter, and asset visuals.
- `lib/battle/types.ts` defines snapshots, commands, events, and the provider.
- `lib/battle/usePresentationQueue.ts` presents ordered events and reconciles
  the provider's final snapshot. Skip invalidates the active run atomically.
- `lib/battle/fixture.ts` is the stateful mock provider.
- `lib/battle/assets.ts` owns all asset and effect lookups.

See `../docs/web-ui/BATTLE_DATA_CONTRACT_V1.md` and
`../docs/web-ui/WEB_UI_ARCHITECTURE.md` for the authority boundary.

## Add content

### Hero

Add the stable definition/combatant identity to the adapter or fixture. Register
its class mapping and requested portrait, figure, and thumbnail paths in
`lib/battle/assets.ts`. Missing requested art falls back to a class icon, then a
generic placeholder/readable initials.

### Skill

Add its presentation metadata to `skillPresentation`: glyph, tone, semantic
effect category, and optional asset. Availability, costs, cooldowns, targets,
and outcomes must still arrive through snapshot `legalActions` and events.

### Status

Add display copy, classification, glyph, and optional icon to `statusRegistry`.
Duration, stacks, application, removal, and tick damage remain provider facts.

### Effect

Register a semantic category in `effectRegistry` and implement its non-
authoritative visual class. Effects may be skipped or reduced and must never
decide an outcome.

## Mock mode and known limits

The mock provider is deliberately stateful so sequential commands and demos
preserve HP, statuses, and summons. Its numbers are fixed fixture outcomes, not
copied battle formulas. Hero art, skill art, and effects are visibly labelled
placeholders. Auto battle is only a local control demonstration. The prototype
targets desktop viewports from 1366×768 through 1920×1080.

## Stage 2 integration

Implement `BattleProvider` against a thin Python adapter. Submit commands with
`expectedRevision`, stable actor/skill IDs, and selected target IDs; return
semantic events plus the complete post-resolution snapshot. Do not parse Python
console prose or recreate rules in TypeScript.
