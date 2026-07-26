# Legends of Champions Tactics — Web UI

The Stage 1.5/2 Web UI is an engine-backed battle client. The Python engine
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

Start the live adapter from the repository root:

```bash
uvicorn battle_api.app:app --reload --port 8000
```

`/` defaults to live Ragnar versus Nighthawk. Override the adapter origin with
`NEXT_PUBLIC_BATTLE_API_URL` (default `http://localhost:8000`). In development,
the isolated toolbar exposes live 1v1 and fixture-backed 1v1/2v2/3v3. Direct
queries are `?provider=live&format=1` and `?provider=mock&format=1|2|3`.

## Component and data shape

- `components/battle/BattleScreen.tsx` is the provider-injected generic screen.
- `components/battle/MockBattleScreen.tsx` adds fixture-only demo controls.
- `components/battle/BattleExperience.tsx` selects the provider and development
  preview without leaking mode branches into generic components.
- `components/battle/` contains hero, skill, status, meter, and asset visuals.
- `lib/battle/types.ts` defines snapshots, commands, events, and the provider.
- `lib/battle/usePresentationQueue.ts` presents ordered events and reconciles
  the provider's final snapshot. Skip invalidates the active run atomically.
- `lib/battle/fixture.ts` is the stateful mock provider.
- `lib/battle/liveProvider.ts` owns HTTP/session behavior and structured errors.
- `lib/battle/formations.ts` is the sole duel/duo/trio formation registry.
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

## Live-state behavior

The UI distinguishes loading, disconnected, rejected, stale-revision, and
adapter-error states. Rejections reconcile any supplied authoritative snapshot.
Gameplay state is never optimistic.

The adapter registry is process-local and should run with one worker. Separate
UI/API origins require adapter CORS configuration or a same-origin proxy. Live
2v2/3v3 scenarios are intentionally out of scope; those layouts use fixtures.
