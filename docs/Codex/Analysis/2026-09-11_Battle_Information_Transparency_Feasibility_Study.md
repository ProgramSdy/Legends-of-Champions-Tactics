# Battle Information Transparency — Feasibility Study

**Task:** STUDY-001  
**Date:** 2026-09-11  
**Status:** Research complete; no implementation authorised  
**Scope:** Analysis only. No production, UI, API, test, data, configuration, or
gameplay files were changed for this study.

## Executive recommendation

Battle Information Transparency is feasible only as an **engine-owned,
non-mutating, explicitly audited** capability. It is not safe to calculate
combat outcomes in React, and it is not safe to call the existing skill
execution path as a “dry run.” Current skills combine random rolls with HP,
status, cooldown, log, turn, and secondary-effect mutation.

The recommended future path is a small, additive engine evaluator whose pure
rule primitives are shared with a limited allowlist of migrated skill
resolutions. The adapter may then serialize those facts to the UI at the
current battle revision. The UI should only render the supplied facts.

The first MVP should cover only audited direct damage and direct healing skills
where the engine can truthfully supply a target-specific range and clearly
separate: damage variation, evasion, deterministic prevention, and status/proc
probability. Chained outcomes, future damage-over-time totals, random spreads,
and any skill that still requires mutating execution to evaluate must be shown
as unavailable or omitted. Do not imply full-roster coverage.

Owner approval is required before any implementation task.

## Evidence classification

- **Confirmed current behaviour** is supported by file/function paths below.
- **Inference** means a conclusion drawn from the current architecture, not an
  implemented contract.
- **Future proposal** is deliberately unapproved design guidance.

## Confirmed current state

### Action and mutation path

1. `battle_api/app.py` `submit_command` sends a command into the adapter worker
   path. `battle_api/adapter.py` `submit()` locks the session, installs its
   saved RNG state, validates the command, calls `_resolve()`, saves the
   resulting RNG state, and restores process-global RNG.
2. Adapter `_validate()` and `_legal_actions()` enforce revision, active actor,
   available skill, side, exact legal target IDs, target count, and formation
   screening. `snapshot()` publishes this legality/state information but no
   prospective outcome.
3. `_resolve()` calls `Skill.execute()` (`skills/skill.py`). Execution performs
   evasion/immunity checks, calls hero skill callbacks, emits mutations/events,
   advances turn/round state, and can run automatic turns.
4. `Hero.take_damage()`, `take_damage_action()`, and `take_healing()` in
   `heroes/hero.py` are mutation boundaries. Damage applies formation
   adjustment, prevention/absorption/on-damage interactions and defeat logic;
   healing applies boosts/reductions, rounding, and the HP cap. Status updates
   are stateful in `game/status_effect_manager.py`.

Therefore `Skill.execute()`, `resolve_targets()`, adapter `_resolve()`, and
status-update methods are not preview APIs.

### Randomness, evasion, prevention, and accuracy

- There is no coherent current attacker Accuracy model. The future Accuracy
  discussion in `docs/ChatGPT/2026-09-06_Strategy_Randomness_Information_and_Accuracy_Design_Discussion.md`
  remains unresolved design discussion, not existing rules.
- `Skill.evasion_check()` derives target evasion from agility/capability and
  rolls `random.randint(1, 100)`. In `Skill.resolve_targets()` evasion is
  evaluated before all-damage, physical, magical, and control immunity.
- A status application/proc roll is separate from evasion. For example Rogue
  Sharp Blade has a separate bleed chance and Poisoned Dagger has a separate
  poison chance. Neither is a final hit chance.
- Immunity/prevention is not uniformly serialized. The adapter has a dedicated
  `damagePrevented` path for Shield of Protection, while other prevention or
  absorption paths are not equivalently exposed.

**Consequence:** do not show a generic “Hit Chance.” At most, a future
authoritative evaluator could supply a narrowly defined `Evade chance` or an
owner-approved reliability label. It must never fold status-proc probability,
random damage variation, or unresolved Accuracy semantics into that value.

### Current frontend boundary

`web-ui/components/battle/BattleScreen.tsx` keeps selected skill, selected
target IDs, and `hoveredTargetId` as local presentation state. Its real figure
buttons use the adapter-provided `legalActions[].validTargetIds`; pointer hover
and keyboard focus share the same hover state and Enter/Space selects a target.
Commands contain revision, actor, skill, and target IDs only.

The frozen contract (`web-ui/lib/battle/types.ts`,
`docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`) includes present HP/statuses and
legal-action data, but not defence/resistance, prospective damage/healing,
evasion, prevention, proc chance, or effect outcome facts. The existing web UI
architecture explicitly places combat resolution, RNG, damage, healing,
immunity, and legality in Python/adapter authority.

**Consequence:** the browser can truthfully trigger and display a preview but
cannot calculate one. Parsing skill descriptions or status presentation text
would be formula duplication and unsafe.

## Representative feasibility matrix

| Representative skill/outcome | Confirmed previewable facts today | Why an exact universal preview is not currently safe | Safe future presentation boundary |
| --- | --- | --- | --- |
| Mage Fireball | Current target HP, legal target, raw variation source; formation and fire-resistance inputs exist in engine | Evasion, immunity, shells, Void Connection, and on-damage effects can change actual HP loss | Audited direct range only after shared pure primitive; separate prevention/evasion facts if authoritative |
| Mage Arcane Missiles | Legal living target set; raw shared variation source | One variation can be shared across targets, while evasion/immunity are per target; multi-target outcome is correlated | Per-target audited range; no aggregate hit percentage; evaluate against the complete selected target set |
| Rogue Sharp Blade | Direct raw band; distinct 50% bleed application roll | Live callback currently does not propagate attack-type/formation metadata; later DoT amount is random | Direct band only if current live behavior is preserved and audited; list bleed separately as conditional, never total DoT |
| Rogue Poisoned Dagger | Direct band; explicit 85% poison application roll and current stack state | Poison tick and resistance interactions are future/random; cap/refresh matters | Direct range plus separate “may apply/add Poison” fact only when status semantics are audited |
| Priest Binding Heal | Target/current HP; raw selected-target range; separate self-heal branch | Effective restored HP depends on boost/reduction, rounding, missing HP, and second independent roll | Prefer effective target range after cap; show self-heal separately only when evaluator can supply it |
| Priest Discipline Penance | Target side and legal target context | Ally branch heals; enemy branch damages via its own evasion path; Redemption can cause chained healing | Server chooses `healing` or `damage` by target side; omit chain total unless audited |
| Shadow Word Pain | Direct range source and present/absent mark state | Evasion/immunity gates application and later DoT may be random | Direct band and conditional “applies Pain if it lands and target is unmarked”; no future total |
| Shadow Evasion / passive / targetless skill | Availability and skill metadata | No target-hover outcome; execution mutates self/cooldown | No target panel; optionally later use a separate skill-level fact card |
| Shield, immunity, damage split, spread, on-defeat chain | Present state may be visible in part | Effects occur inside mutating damage/defeat paths and are not all serialized | Only deterministic prevention explicitly proven by evaluator; otherwise unavailable/conditional |

## Architecture options

| Option | Correctness and mutation risk | UX/latency | Contract/maintenance | Assessment |
| --- | --- | --- | --- | --- |
| Execute existing skill path then restore state | Unsafe: global/session RNG, logs, event cursors, secondary recipients, circular graphs, cooldowns and status changes can escape restoration | May appear immediate but corrupts determinism | No clean contract, fragile forever | Reject |
| Clone live state and simulate | Less direct mutation, but still consumes/controls RNG and can reveal exact next seeded outcomes; deep clone fidelity is difficult | Expensive and difficult for hover | Large hidden simulation surface | Do not use for MVP |
| Pure engine evaluator shared with resolution primitives | Strongest long-term authority once individual skills are migrated/audited | Server round-trip must be managed; can prefetch after skill selection later | Additive adapter contract; one rule source | Recommend |
| Adapter preview endpoint over the pure evaluator | Preserves adapter validation, session lock, and revision ownership | On-demand request is simple; batch/preload can be evaluated later | Typed additive response and provider integration | Recommend as delivery boundary |
| React/display-only calculation from snapshot | Incorrect: snapshot lacks inputs and formulas are skill-specific/legacy-inconsistent | Instant but misleading | Creates second combat engine and drift | Reject |

### Recommended staged path — future proposal

1. Inventory and classify skills. Migrate only owner-approved, auditable direct
   damage/healing skills to pure outcome/range primitives shared with their
   mutating executors.
2. Add an engine-owned evaluator that accepts validated battle facts without
   rolling RNG or mutating anything. It must explicitly declare unsupported
   outcomes.
3. Add an adapter-owned, revision-bound preview operation. Validate
   `{expectedRevision, actorId, skillId, targetIds}` using the same
   legal-action authority as a command, take the session lock, and return
   facts at the unchanged revision.
4. Add display-only LiveBattleProvider and BattleScreen integration after the
   engine/API proof exists. Do not put formulas, status interpretation, or
   target legality calculations in TypeScript.
5. Expand coverage only skill-by-skill after pure evaluation and validation
   prove the labels honest.

## Proposed player experience — future proposal

### Compact hierarchy

At most four compact layers:

1. `SKILL → TARGET`
2. Primary result: `Damage 18–29`, `Healing 20–26`, or `Blocked`
3. `HP 21 / 93`
4. One or two material consequences, with their own certainty: `Bleed: 50%`,
   `Applies Healing received −70%`, or `May be evaded`

Omit fields that cannot be authored honestly. Never convert absence of a miss
model into `100%`, and never display raw base healing as effective restored HP
when the target is at/near maximum HP.

| Situation | Example copy |
| --- | --- |
| Direct damage | `FATAL STRIKE → Ragnar` · `Damage 18–29` · `HP 21/93` · `Applies Healing received −70%` |
| Direct heal | `BINDING HEAL → Thorin` · `Healing 20–26` · `HP 45/109` · `Also heals caster 12–16` (only if separately evaluated) |
| Damage plus proc | `SHARP BLADE → Target` · `Damage 12–19` · `Bleed: 50%` |
| Proven deterministic prevention | `BLOCKED — Shield of Protection` · `Damage 0` |
| Multi-target/flexible | `ARCANE MISSILES · TARGET 1 OF 2`; show hovered target facts and selected-target chips. `PENANCE` says `Healing` for ally or `Damage` for enemy only from server-authored target facts. |

### Interaction and accessibility rules

- Desktop: show beside the focused/hovered legal target; do not cover the
  figure control or enter its hit-test stack (`pointer-events: none`). Keep the
  existing gold target cues.
- Keyboard: focus should produce the same preview as hover. Keep focus on the
  target button, connect it with `aria-describedby`, expose selected state, and
  avoid noisy live announcements on every pointer movement.
- Touch/compact landscape: first legal-target tap selects and pins a stable
  details panel; a different legal target replaces or extends it according to
  target cardinality. The Battle Scene’s existing portrait guard remains.
- Hide/clear preview if commands are not accepted, a presentation is playing,
  the skill is unavailable/passive/targetless, the actor/skill/revision changes,
  or target legality changes. On unavailable/error, say `Preview unavailable`
  without blocking an otherwise legal action.
- The battle scene is a constrained `100dvh` HUD. At narrow modes use a stable
  reserved edge/command-dock panel rather than a detailed sidebar or a popover
  that blocks hero artwork.

## Proposed future contract sketch — unapproved

This is a contract sketch, not an endpoint or approved API change.

```ts
type BattlePreviewRequest = {
  expectedRevision: number;
  actorId: string;
  skillId: string;
  targetIds: string[];
};

type BattlePreview = {
  revision: number;
  actorId: string;
  skillId: string;
  targetIds: string[];
  coverage: "authoritative" | "unavailable";
  reasonId?: string;
  targets: Array<{
    targetId: string;
    currentHp: number;
    maxHp: number;
    primary: {
      kind: "damage" | "healing" | "prevented" | "none";
      amountRange?: { min: number; max: number };
      effectiveAmountRange?: { min: number; max: number };
    };
    reliability?:
      | { kind: "guaranteed" }
      | { kind: "evasion"; percent: number }
      | { kind: "conditional"; reasonId: string }
      | { kind: "unknown" };
    consequences: Array<{
      kind: string;
      certainty: "guaranteed" | "conditional" | "unknown";
      chancePercent?: number;
      duration?: number;
    }>;
  }>;
};
```

The future API must be additive, typed in Python and TypeScript, revision-bound,
and provider-owned. The frontend must render supplied labels/facts rather than
recreate values from current HP, descriptions, statuses, faculty, or formation.

## Future validation plan — no implementation performed

| Area | Required future proof |
| --- | --- |
| No mutation | Deep-compare HP, stats, statuses, stacks/durations, cooldowns, positions, turn state/queues, revision, events, logs/cursors, command results, recycle/summon links, adapter snapshot, session RNG and `random.getstate()` before/after preview. |
| No RNG consumption | Patch `random.randint`, `random.random`, `choice`, `sample`, and `shuffle` to fail during pure preview. Repeat preview and prove a later same-seed command produces the same result as an untouched clone. |
| Range truth | On separate controlled seeded resolution, actual direct/effective outcome lies in the audited range only where the skill semantics support a range. Test min/max/proc/evasion boundaries. |
| Legality/staleness | Reject battle-not-found, stale revision, inactive actor, unavailable skill, wrong side, dead target, duplicate target, and insufficient/extra multi-target sets without mutation. |
| Combat conditions | Cover 1v1, 2v2 Front/Rear and Side-by-Side, every approved 3v3 formation, full-HP healing, zero damage, immunity, absorption, evasion-before-immunity ordering, flexible Penance sides, DoT/status cap/refresh, chains, cooldowns, and targetless skills. |
| UI/accessibility | Verify mouse, focus/keyboard, touch, rapid hover/request cancellation, loading/error/stale clearing, auto/presentation-disabled state, all supported landscape configurations, pointer hit areas, reduced motion, and server values rendered without client formulas. |

## Risks, non-goals, and owner decisions

### Risks and mitigations

- **State/RNG corruption:** forbid executing live mutating code for preview;
  use pure shared primitives and prove equivalence.
- **False precision:** introduce fields only with a cited authoritative source;
  otherwise omit or mark unavailable.
- **Formula drift:** no React formulas; UI consumes adapter facts only.
- **Stale results:** bind preview to revision, actor, skill, and complete target
  IDs; reject or clear on any mismatch.
- **Partial coverage:** communicate the audited-skill boundary, not a generic
  all-hero promise.

### Non-goals

- No Accuracy, Evasion, damage, healing, status, target, RNG, balance, or
  gameplay-rule change.
- No worksheet of hidden stats/intermediate arithmetic.
- No endpoint, UI, or rollout commitment from this study.

### Owner decisions required before implementation

1. Whether current evasion-derived information should be displayed at all, and
   its player-facing label before an Accuracy model is approved.
2. MVP allowlist: audited direct ranges only, or which conditional effects are
   worth adding first.
3. Whether prevention should show `Blocked`/`Damage 0` only where
   deterministic, despite current evasion-first resolution ordering.
4. Whether healing means attempted amount, effective restored HP, or both.
5. How to present uncertain chains/spreads and multi-target results: omit,
   qualitative explanation, per-target facts, or a compact aggregate.
6. On-demand versus revision-scoped/batched previews after latency and payload
   measurement.
7. Whether/when to normalize legacy skill paths (including shared pure
   primitives and missing attack-type propagation) before expanding scope.

## Research participation and review

All five selected roles were dispatched for research only:

- **Project manager:** evidence/dependency map, decision gates, risk controls,
  report structure, and owner-decision list.
- **Game engine developer:** authoritative resolution/RNG/mutation trace,
  representative feasibility evidence, and architecture comparison.
- **UI developer:** current hover/focus/touch/responsive boundary, compact
  panel hierarchy, accessibility, and frontend authority limits.
- **Test automator:** future no-mutation/no-RNG and deterministic validation
  matrix.
- **Reviewer:** independently required that the report avoid generic exact
  feasibility, accuracy/proc conflation, raw-heal overclaiming, and client-side
  calculation; the report incorporates those guardrails.

**Independent review disposition:** approved as a study-only report with an
engine-owned audited MVP recommendation. No production implementation should
begin without owner approval.
