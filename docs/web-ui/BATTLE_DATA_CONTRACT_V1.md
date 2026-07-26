# Web UI Battle Data Contract v1

Status: Frozen v1 contract, implemented by both the Stage 1 mock provider and
the Stage 2 Python adapter. The existing engine remains authoritative.

## Scope and evidence

The active engine is a mutable in-process graph rather than a serializable API.
`Game` owns the round, current actor, team lists, living heroes, action queue,
and battle state (`game/game.py`). `Hero` owns HP, generated statistics,
statuses, buff/debuff records, skills, and summon metadata (`heroes/hero.py`).
`Skill` owns target metadata and cooldown state, but also resolves evasion and
immunity before dispatching the concrete skill method (`skills/skill.py`).

Representative Stage 1 rules are split across:

- `heroes/necromancer.py`: Summon Flesh Puppet, Life Drain, Stitch of Agony.
- `heroes/warlock.py`: Shadow Bolt.
- `heroes/summon_unit.py`: the Flesh Puppet skills named `Flesh Slam Single`
  and `Flesh Slam Multi`; their emitted prose currently says "Flash Slam".
- `game/status_effect_manager.py`: round-start Stitch of Agony ticks and status
  expiry.

The engine has no mana or generic secondary-resource model. Skill descriptions,
icons, visual effect categories, mana costs, and the concept image's resource
bars are therefore presentation metadata in Stage 1, not engine facts. The UI
must label fixture-only costs/resources as placeholders or omit them. A future
engine-backed resource cannot be inferred or decremented by React.

## Transport envelope

Every adapter response uses a versioned envelope. JSON field names use
`camelCase`; identifiers are opaque lower-case strings.

```ts
type BattleEnvelope<T> = {
  contractVersion: "1.0";
  battleId: string;
  revision: number;       // monotonically increases after authoritative change
  serverTime?: string;    // ISO 8601; informational only
  data: T;
};
```

The Stage 1 mock provider implements this shape locally. The Stage 2 Python
adapter now exposes it over JSON HTTP. Future transports may also expose the
same versioned envelope over WebSocket, IPC, or an in-process bridge without
changing component props.

## Stable identifiers

Do not use display names or array indices as identity.

- Definition IDs identify reusable game definitions:
  `hero.necromancer.flesh_puppeteer`,
  `hero.warlock.comprehensiveness`, `summon.flesh_puppet`,
  `skill.summon_flesh_puppet`, `skill.life_drain`,
  `skill.stitch_of_agony`, `skill.shadow_bolt`,
  `skill.flesh_slam_single`, and `skill.flesh_slam_multi`.
- Combatant IDs identify one runtime instance:
  `friendly.arthas`, `friendly.black_heart`,
  `friendly.arthas.flesh_puppet.1`, `enemy.sashein`, and
  `enemy.andonidas`.
- Status IDs identify definitions, for example `status.stitch_of_agony` and
  `status.shadow_bolt`.
- Event and command IDs are unique within a battle, for example
  `evt.000014` and `cmd.000003`.

These fixture IDs are stable test/API IDs, not claims that the Python repository
already supplies IDs. The adapter must maintain object-to-combatant-ID mapping
for the lifetime of a battle. Summon IDs use a per-master, per-definition
monotonic ordinal and are never reused after defeat/removal.

Display mapping for the approved fixture:

| Combatant ID | Display | Engine class/major |
|---|---|---|
| `friendly.arthas` | Arthas | `Necromancer_Flesh_Puppeteer` |
| `friendly.black_heart` | Black Heart | `Warlock_Comprehensiveness` |
| `friendly.arthas.flesh_puppet.1` | Arthas's Flesh Puppet | `FleshPuppet` / `Flesh_Puppet` |
| `enemy.sashein` | Sashein | `Necromancer_Flesh_Puppeteer` |
| `enemy.andonidas` | Andonidas | a Mage specialization selected by the fixture |

`Flash Slam` is presentation copy only. Commands must use one of the actual
engine skills, `skill.flesh_slam_single` or `skill.flesh_slam_multi`.

## Authoritative snapshot

```ts
type BattleSnapshot = {
  phase: "initializing" | "roundStart" | "awaitingCommand" |
         "resolving" | "roundEnd" | "ended";
  round: number;
  turn: { index: number; total: number };
  activeCombatantId: string | null;
  outcome: null | {
    kind: "victory" | "draw" | "roundLimit";
    winningSideId: "friendly" | "enemy" | null;
  };
  sides: Array<{
    id: "friendly" | "enemy";
    combatantIds: string[]; // stable slot order, including summons
    maxSlots: number;
  }>;
  combatants: Record<string, CombatantState>;
  turnOrder: Array<{
    combatantId: string;
    hasActed: boolean;
    isCurrent: boolean;
  }>;
  legalActions: LegalAction[]; // commands currently available to the client
};

type CombatantState = {
  id: string;
  definitionId: string;
  sideId: "friendly" | "enemy";
  slot: number;
  displayName: string;
  faculty: string;
  specialization: string;
  isSummon: boolean;
  masterCombatantId: string | null;
  summonRoundsRemaining: number | null;
  isPlayerControlled: boolean;
  alive: boolean;
  hp: { current: number; maximum: number };
  resource: null | {
    kind: string;
    current: number;
    maximum: number;
  };
  statuses: Array<{
    id: string;
    instanceId: string;
    kind: "buff" | "debuff" | "control" | "other";
    roundsRemaining: number | null;
    stacks: number | null;
    sourceCombatantId: string | null;
  }>;
  skills: Array<{
    id: string;
    displayName: string;
    targetMode: "none" | "self" | "singleAlly" | "singleEnemy" |
                "multipleAllies" | "multipleEnemies" | "flexible";
    maximumTargets: number;
    cooldownRemaining: number;
    available: boolean;
    unavailableReason: string | null;
    resourceCost: null | { kind: string; amount: number };
  }>;
};

type LegalAction = {
  skillId: string;
  actorId: string;
  minimumTargets: number;
  maximumTargets: number;
  validTargetIds: string[];
};
```

Only `legalActions` determines whether a skill/target can be commanded. The
client may calculate bar width from authoritative current/maximum values and
may disable controls using `legalActions`; it may not derive legality from
skill labels, status names, cooldown math, or HP.

An `awaitingCommand` snapshot may expose legal actions before command
submission; these entries communicate the actor, skills, and targets the client
can currently submit. After an accepted command, the returned final snapshot
contains the legal actions for the next authoritative actor when another
command is available, or an empty array when no command is currently legal,
including after the battle has ended.

The adapter maps the engine's five string states onto `phase`. `turn.index` is
the current completed/active position in the round and is adapter-owned because
the engine has no explicit turn counter. `turn.total` and `turnOrder` come from
the current action queue plus already-actioned living combatants. A newly
summoned unit may enter the current engine action queue and must then appear in
an updated snapshot.

Status serialization must be an explicit mapping from engine flags and
`Buff`/`Debuff` records. The UI must never enumerate arbitrary Python
attributes or guess durations by naming convention.

## Commands

```ts
type BattleCommand =
  | {
      type: "useSkill";
      commandId: string;
      expectedRevision: number;
      actorId: string;
      skillId: string;
      targetIds: string[];
    }
  | {
      type: "endTurn";
      commandId: string;
      expectedRevision: number;
      actorId: string;
    };

type CommandResult =
  | { accepted: true; commandId: string; revision: number;
      events: BattleEvent[]; snapshot: BattleSnapshot }
  | { accepted: false; commandId: string; revision: number;
      code: "staleRevision" | "notYourTurn" | "illegalSkill" |
            "illegalTargets" | "battleEnded" | "invalidCommand";
      message: string; snapshot: BattleSnapshot };
```

Speed, auto-battle, selected skill, hovered target, cleared log, fullscreen,
and animation skipping are client preferences, not battle commands. Stage 1
`endTurn` is exposed only when the provider supplies it as a legal interaction;
the current Python player flow otherwise expects skill execution.

Commands express intent only. The adapter resolves combat through the engine,
then returns semantic events and a final authoritative snapshot. Duplicate
`commandId` values must be idempotent. `expectedRevision` prevents input
against stale state. Rejection never mutates authoritative state.

## Semantic events

```ts
type BattleEvent = {
  id: string;
  sequence: number;
  type:
    | "battleStarted" | "roundStarted" | "turnStarted"
    | "skillStarted" | "characterMoved" | "projectileLaunched"
    | "damageApplied" | "healingApplied"
    | "statusApplied" | "statusRemoved" | "attackEvaded"
    | "characterSummoned" | "characterDefeated"
    | "turnEnded" | "battleEnded";
  sourceId?: string;
  targetId?: string;
  targetIds?: string[];
  skillId?: string;
  statusId?: string;
  amount?: number;
  hpAfter?: { current: number; maximum: number };
  roundsRemaining?: number | null;
  combatant?: CombatantState;
  movement?: "lunge" | "return" | "offset";
  effectHint?: "magic" | "healing" | "melee" | "status" | "summon";
  message: string; // adapter-authored display text; never parsed for state
};
```

Fields irrelevant to an event are omitted. State-changing events include their
post-change value (`hpAfter`, status duration, or full summoned combatant).
`attackEvaded` has no `amount` or HP mutation. One Life Drain resolution can
produce ordered damage and healing events. Flesh Slam Multi can produce
multiple target damage events followed by self-damage. Stitch of Agony produces
`statusApplied` on cast and later `damageApplied` events at authoritative
round-start processing.

`characterMoved` and `projectileLaunched` are semantic presentation cues. They
may be synthesized by the adapter from a versioned skill-presentation registry;
they never change rules. Unknown event types must be logged and skipped safely,
then the final snapshot reconciled.

## Presentation and reconciliation

The provider returns events in strict `sequence` order plus the post-resolution
snapshot. The UI queues events, presents each at the selected local speed, and
temporarily blocks battle input while required. It may shorten, skip, or replace
missing effects and must honor `prefers-reduced-motion`.

For smooth bars, visible state may apply each event's post-change value during
playback. After the queue completes—or immediately after interruption,
unknown/malformed events, reload, or reconnection—the UI replaces visible state
with the returned snapshot. Animation completion is never an acknowledgement
required by the engine.

Battle-log entries are rendered from `event.message` and event type. Console
strings in `Game.output_buffer` are not a contract and must not be parsed.

## Authority boundary

Python/adapter authority:

- random rolls, generated statistics, damage, healing, evasion, immunity;
- legal actors, skills and targets;
- cooldown start/decrement/completion;
- status application, duration, tick, stack, removal, and classification;
- summon creation, slot/team membership, lifetime, and same-round action;
- action/turn order, round transitions, defeat, victory, and draw;
- all resource values/costs if a resource system is later added.

UI authority:

- selected/hovered controls before submission;
- event playback timing, camera/effect choice, local speed and reduced motion;
- asset lookup/fallback, tooltips, truncation, layout, log visibility;
- optimistic highlighting only (never optimistic HP, status, cooldown, summon,
  turn, resource, defeat, or victory changes).

Mock-provider authority:

- fixed snapshots and scripted event outcomes for UI demonstration only;
- placeholder descriptions/assets/effect hints and clearly marked
  non-authoritative resource metadata.

Mock data lives behind the same provider interface and must not introduce
fixture checks into components. Production integration requires an adapter that
captures mutations as structured events. Parsing existing prose is explicitly
out of scope because it is incomplete, ANSI-decorated, and unstable.

## Stage 1 fixture acceptance

The versioned fixture should include the five named base combatants above, with
the Flesh Puppet initially absent or in an empty friendly slot. Its scripts
must demonstrate:

1. Life Drain: `skillStarted`, magic cue, damage, and healing.
2. Stitch of Agony: damage if resolved by the engine, status application, and
   a later authoritative tick/removal.
3. Shadow Bolt: magic projectile, damage or evade, and status application when
   applicable.
4. Summon Flesh Puppet: summon event with a new instance ID and updated turn
   order/snapshot.
5. Flesh Slam: movement/impact, enemy damage, and self-damage where the
   multi-target engine skill is used.

Fixture numbers are intentionally test data, not duplicated formulas. Every
script terminates with a complete snapshot so event-sequencer tests can verify
reconciliation.

## Stage 2 live adapter

`battle_api.adapter.BattleAdapter` implements this contract for the whitelisted
`ragnar-vs-nighthawk` scenario. Accepted commands invoke the repository's
existing `Skill.execute` method; the adapter does not reproduce damage, evade,
cooldown, status, or round formulas. Semantic events are built from typed
pre/post engine state captured around skill and round-start mutation boundaries,
never from `Game.output_buffer`.

The development transport is JSON HTTP:

- `GET /api/v1/health`
- `POST /api/v1/battles`
- `GET /api/v1/battles/{battleId}`
- `POST /api/v1/battles/{battleId}/commands`

Sessions are process-local and disappear on restart. A session stores its own
Python `random` state; the adapter swaps that state around engine calls under a
session lock. This makes seeded single-session tests reproducible without
changing rule probabilities, but it is not a substitute for durable replay or
multi-process persistence.

Open design decisions remain: durable session storage, cross-process locking,
hidden-information policy, localization ownership, durable replay/audit,
production authentication, and whether a real resource system is planned.
