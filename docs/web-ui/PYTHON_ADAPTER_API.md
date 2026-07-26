# Python battle adapter and API

## Runtime

Install `requirements.txt` plus `requirements-api.txt`, then start the
development API from the repository root:

```bash
uvicorn battle_api.app:app --reload --port 8000
```

Development CORS allows exactly `http://localhost:3000` and
`http://127.0.0.1:3000` by default. Override the exact allowlist with a
comma-separated environment variable:

```bash
BATTLE_API_CORS_ORIGINS=http://localhost:3001,http://127.0.0.1:3001 \
  uvicorn battle_api.app:app --reload --port 8000
```

Wildcard origins are ignored and credentials are disabled. Production origins
must therefore be explicitly configured.

The FastAPI handlers are async and perform no database or network I/O. They
offload synchronous legacy-engine work through `asyncio.to_thread`; resolution
is protected by per-session and module-global RNG locks, so it does not block
the ASGI event loop or interleave the engine's module-global random state.

## Endpoints

### `GET /api/v1/health`

Returns service and contract version health.

### `POST /api/v1/battles`

Request:

```json
{"scenarioId": "ragnar-vs-nighthawk", "seed": 42}
```

Only the listed scenario is accepted. `seed` is optional. The response is a v1
envelope whose data contains initial semantic events and the full snapshot.

### `GET /api/v1/battles/{battleId}`

Returns the current authoritative snapshot. Unknown IDs return HTTP 404 with a
structured `battleNotFound` detail.

### `POST /api/v1/battles/{battleId}/commands`

Request:

```json
{
  "type": "useSkill",
  "commandId": "cmd.browser.1",
  "expectedRevision": 0,
  "actorId": "enemy.nighthawk",
  "skillId": "skill.rogue.sharp_blade",
  "targetIds": ["friendly.ragnar"]
}
```

Rule-level rejections return HTTP 200 with `accepted: false`, a stable rejection
code, and the current snapshot. This lets the client reconcile stale state.
Malformed JSON is HTTP 422 and missing battles are HTTP 404. Duplicate command
IDs return the originally stored result without resolving the engine again.

## Source and rule mapping

| Contract definition | Exact Python source | Constructor / engine skills |
|---|---|---|
| `hero.warrior.weapon_master` / Ragnar | `heroes.warrior.Warrior_Weapon_Master` | `(sys_init, "Ragnar", "Group_A", True)`; Fatal Strike, Armor Crush, Antivenom Potion |
| `hero.rogue.comprehensiveness` / Nighthawk | `heroes.rogue.Rogue_Comprehensiveness` | `(sys_init, "Nighthawk", "Group_B", True)`; Sharp Blade, Poisoned Dagger, Shadow Evasion |
| Battle state and rounds | `game.game.Game` | `Game([ragnar], [nighthawk], "simulation")`, `game_initialization`, `start_round`, `end_round` |
| Target/evasion dispatch | `skills.skill.Skill` | `Skill.execute` and `Skill.resolve_targets` |
| Damage/defeat | `heroes.hero.Hero` | `take_damage`, `take_damage_action`, `check_if_defeated` |
| Round status/cooldown | `game.status_effect_manager.StatusEffectManager`, `Game.update_battle_information` | invoked by `Game.start_round` |

Target rules come from `Skill.target_qty`, `target_type`, `skill_type`, and the
engine-maintained living allies/opponents lists. Fatal Strike, Armor Crush,
Sharp Blade, and Poisoned Dagger require one living enemy. Antivenom Potion and
Shadow Evasion are targetless self buffs. There is no mana/resource system.

Fatal Strike applies healing reduction. Armor Crush applies/extends armor break
and can add bleeding/wound effects. Antivenom Potion heals, boosts poison
resistance, dispels supported bleeding/toxic effects, and starts a three-round
engine cooldown. Sharp Blade can apply bleeding. Poisoned Dagger can apply and
stack poison. Shadow Evasion grants temporary evasion and starts a two-round
engine cooldown. Other listed skills have no generic cooldown in their class
implementations.

## Known limitations and defects

- Hero construction depends on the two Excel workbooks under `data/`. The
  adapter uses a headless loader and intentionally avoids Pygame/image setup.
- The engine uses module-global `random`. Sessions retain independent RNG state
  and a module-global lock prevents cross-session interleaving. This is safe for
  the current process, but an engine-owned RNG dependency would scale better.
- The legacy `Skill.execute` API represents targetless buffs with the sentinel
  `["none"]`; the adapter contains this narrow compatibility mapping.
- Event capture covers the selected heroes' explicit status registry. Expanding
  the whitelist requires adding stable status/source mappings; arbitrary Python
  attributes are never exposed.
- The process-local registry has no persistence, authentication, expiry, quota,
  or multi-worker consistency. Run one API worker for this milestone.
- Rejections do not mutate engine state. Unexpected exceptions are not yet
  converted to a public adapter-error response; FastAPI returns its normal 500.
