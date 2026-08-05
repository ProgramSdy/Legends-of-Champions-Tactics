# Python battle adapter and API

## Runtime

Install `requirements.txt` plus `requirements-api.txt`, then start the
development API from the repository root:

```bash
make dev
```

`make dev` starts the adapter on port 8001 and the web client on port 3001;
press Ctrl-C once to stop both. To run the adapter independently, use:

```bash
uvicorn battle_api.app:app --reload --port 8001
```

### Same-Wi-Fi development access

For a temporary local-network playtest, run this from the repository root:

```bash
make lan
```

It detects the Mac Wi-Fi address from `en0`, binds the development frontend and
adapter to the LAN, configures the browser to use that same host for the API,
and restricts API CORS to that explicit browser origin plus the two local
origins. If Wi-Fi is on another interface, provide the address yourself:

```bash
make lan LAN_HOST=192.168.1.42
```

Open `http://<LAN_HOST>:3001` from another device on the same trusted network.
Allow incoming connections for ports 3001 and 8001 in macOS Firewall if asked.
This is an unauthenticated development mode, not an Internet-facing deployment:
do not use it on untrusted/shared networks or forward these ports through a
router.

Development CORS allows exactly `http://localhost:3001` and
`http://127.0.0.1:3001` by default. Override the exact allowlist with a
comma-separated environment variable:

```bash
BATTLE_API_CORS_ORIGINS=http://localhost:3001,http://127.0.0.1:3001 \
  uvicorn battle_api.app:app --reload --port 8001
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

### `GET /api/v1/heroes`

Returns contract version `1.0` and exactly the eight approved hero definitions,
including stable `definitionId`, display name, faculty, and specialization.
The roster display name is catalogue metadata. Each non-summoned battle
combatant receives a runtime name from its class's `HeroGenerator` faculty pool
during session creation.

### `POST /api/v1/battles`

Request:

```json
{
  "battleSize": 3,
  "playerTeam": [
    "hero.priest.comprehensiveness",
    "hero.priest.discipline",
    "hero.paladin.retribution"
  ],
  "enemyCompositionMode": "specified",
  "enemyTeam": [
    "hero.rogue.comprehensiveness",
    "hero.warrior.weapon_master",
    "hero.warrior.defence"
  ],
  "enemyControlMode": "computer",
  "seed": 42
}
```

`battleSize` is 1, 2, or 3. Player and specified-enemy arrays must match that
size and contain only roster IDs. `enemyTeam` is omitted in random mode.
Repeated definitions and cross-team overlap are allowed. `seed` is optional.
The legacy `{"scenarioId":"ragnar-vs-nighthawk"}` request remains accepted.

Random composition is selected inside the adapter with session-seeded
randomness. The response is a v1 envelope containing ordered initial and
computer-turn events plus the snapshot at the next player turn or battle end.
For an automatically resolved opening, it also additively includes
`openingSnapshot` (the authoritative state before automatic opening events are
presented) and `playOpening: true`. The client begins its visible queue from
that snapshot, plays the returned events in order, then reconciles to the
returned final snapshot and revision. Player-first openings retain
`playOpening: false`; their ordinary initial snapshot remains immediately
usable after the entry overlay.

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

When the next actor is computer-controlled, the adapter continues resolving
existing engine AI turns before returning. The accepted response includes all
ordered events, its final revision, and the snapshot at the next player turn or
battle end.

Responses may add `battleLog` events carrying sanitized Python-authored
presentation lines. `channel` is `battleInfo` or `statusUpdate`. Typed semantic
events remain authoritative for mutations and playback; `visibleInLog: false`
only suppresses their generic text when a Python line would duplicate it.

Each `statusApplied` event also includes the additive `statusPresentation`
classification: `buff`, `debuff`, or the compatible `neutral` fallback. The
adapter derives it from authoritative serialized status metadata; control
statuses use the harmful `debuff` presentation. Existing `effectHint: "status"`,
status duration, source and target fields remain unchanged.

`statusApplied` also carries the additive nullable `stacks` field whenever the
serialized post-event status has a stack count. The adapter emits it for a new
status and for a retained status whose stack count, source, kind, or refreshed
duration changes. A duration-only countdown tick does not create a synthetic
status-application event. This changes neither status rules nor the v1 event
ordering; older consumers can ignore the optional field.

Every snapshot includes additive v1 `turnControl`. Its disposition is
`playerCommand`, `automaticAction`, `skip`, or `ended`; commands are accepted
only when `acceptsCommands` is true at a `playerCommand` boundary and the
submitted action matches the published `legalActions`. Automatic and skipped
states are classified by the engine-owned `Hero.turn_directive()` seam rather
than by adapter-local status rules.

Freeze, stun, paralysis, and fear are authoritative automatic skip states.
Affected player or computer actors expose no legal actions; the adapter emits
turn progression events and advances to the next actionable actor.

Scoff is resolved automatically from the engine directive's forced skill and
targets against its living initiator, regardless of the configured control
mode. Normal client actions are not exposed during that forced resolution. A
stale Scoff whose initiator is defeated is removed without consuming the turn.
The initiator is serialized as the status and turn-control source where
applicable.

## Source and rule mapping

| Contract definition | Exact Python source | Constructor / engine skills |
|---|---|---|
| `hero.priest.comprehensiveness` / Aurelia | `heroes.priest.Priest_Comprehensiveness` | Holy Smite, Shadow Word Pain, Binding Heal |
| `hero.priest.discipline` / Seraphine | `heroes.priest.Priest_Discipline` | existing specialization skills and AI |
| `hero.paladin.retribution` / Valerius | `heroes.paladin.Paladin_Retribution` | existing specialization skills and AI |
| `hero.paladin.protection` / Bastion | `heroes.paladin.Paladin_Protection` | existing specialization skills and AI |
| `hero.mage.comprehensiveness` / Lyra | `heroes.mage.Mage_Comprehensiveness` | existing specialization skills and AI |
| `hero.warrior.defence` / Aegis | `heroes.warrior.Warrior_Defence` | existing specialization skills and AI |
| `hero.warrior.weapon_master` / Ragnar catalogue entry | `heroes.warrior.Warrior_Weapon_Master` | runtime Warrior-pool name; Fatal Strike, Armor Crush, Antivenom Potion |
| `hero.rogue.comprehensiveness` / Nighthawk catalogue entry | `heroes.rogue.Rogue_Comprehensiveness` | runtime Rogue-pool name; Sharp Blade, Poisoned Dagger, Shadow Evasion |
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
- Runtime names are selected from `HeroGenerator.hero_classes` inside that
  session random boundary. Same-faculty names are unique across both teams until
  the pool is exhausted, after which creation permits repeats. Name selection
  derives from then restores the session stream before hero construction;
  equal seeds/configurations remain reproducible without shifting established
  combat/stat rolls.
- The legacy `Skill.execute` API represents targetless buffs with the sentinel
  `["none"]` and has different scalar/list target shapes; the adapter contains
  narrow compatibility mappings.
- Event capture covers the approved heroes' explicit status registry. Expanding
  the whitelist requires adding stable status/source mappings; arbitrary Python
  attributes are never exposed.
- The process-local registry has no persistence, authentication, expiry, quota,
  or multi-worker consistency. Run one API worker for this milestone.
- Rejections do not mutate engine state. Unexpected exceptions are not yet
  converted to a public adapter-error response; FastAPI returns its normal 500.
