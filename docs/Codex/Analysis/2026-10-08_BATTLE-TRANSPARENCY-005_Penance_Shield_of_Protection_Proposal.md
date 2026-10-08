# BATTLE-TRANSPARENCY-005 — Penance / Shield of Protection Study and Proposal

**Date:** 2026-10-08  
**Status:** Rejected by owner on 2026-10-08. Superseded by
[`2026-10-08_BATTLE-TRANSPARENCY-005_Penance_Valid_Direct_Damage_Proposal.md`](2026-10-08_BATTLE-TRANSPARENCY-005_Penance_Valid_Direct_Damage_Proposal.md).  
**Scope:** The opponent-targeted branch of Priest Discipline's Penance when the
target has Shield of Protection, including same-caster Holy Word Redemption
linked healing. This study does not change combat mechanics, preview code,
tests, contracts, or completion records.

## 1. Root cause, with live and preview evidence

The live hybrid `damage_healing` dispatcher checks evasion before it invokes
the Penance callback. A successful evasion returns immediately; otherwise the
callback receives the opponent branch
([`skills/skill.py`](../../../skills/skill.py#L323-L340)).

On a landed opponent Penance, the callback:

1. computes raw 17–21 damage;
2. calls `other_hero.take_damage(damage_dealt, attack_type, self)`;
3. independently calculates `round(redemption.effect * damage_dealt)`; and
4. calls `take_healing` for every ally holding a same-caster Holy Word
   Redemption buff.

The linked-healing loop is not conditional on the damage receipt reducing the
opponent's HP ([`heroes/priest.py`](../../../heroes/priest.py#L529-L556)).
`Hero.take_damage` recognises Shield of Protection and returns an immunity
message without reducing HP, but it does not abort or signal the calling
Penance callback ([`heroes/hero.py`](../../../heroes/hero.py#L637-L875)).
Thus it cannot stop Penance's next linked-healing step.

The present preview special-cases this state as
`prevention.allDamage` in `_evaluate_preview`
([`battle_api/adapter.py`](../../../battle_api/adapter.py#L2058-L2070)). It
then passes `prevented=True` to `_preview_consequences`, whose Discipline
branch returns immediately before calculating `secondaryHealing`
([`battle_api/adapter.py`](../../../battle_api/adapter.py#L1568-L1633)). The
present regression test encodes that incorrect empty consequence list
([`tests/test_battle_transparency_005_preview.py`](../../../tests/test_battle_transparency_005_preview.py#L137-L176)).

This is a presentation-preview defect, not evidence that the underlying combat
mechanic should change.

## 2. Current live outcome versus current preview outcome

| Situation | Live outcome | Current preview outcome | Truthful result needed |
| --- | --- | --- | --- |
| Penance evades | `Skill.execute` does not call Penance; no direct damage and no linked Redemption healing. | Shows normal damage range plus Hit Chance; no deterministic linked-healing guarantee should be presented. | Retain hit chance and make linked healing explicitly **on hit** only. |
| Penance lands; target has Shield of Protection; no same-caster Redemption holder | Direct `take_damage` causes zero HP loss; no linked healing exists. | `Damage 0 · Blocked`, no secondary rows. | Current result is correct. |
| Penance lands; target has Shield of Protection; one or more same-caster Redemption holders | Direct target HP remains unchanged; the callback still heals each holder from the raw Penance damage. | `Damage 0 · Blocked`, **incorrectly no linked-healing rows**. | `Damage 0 · Blocked` **plus** one `secondaryHealing` row per eligible recipient, each `certainty: onHit`. |
| Penance lands; ordinary target; same-caster Redemption holder(s) | Direct damage applies; each holder receives its linked healing. | Normal direct damage and linked rows. | Retain current behaviour. |

The direct hit chance remains relevant in the protected state: evasion occurs
before the callback. A protected target therefore does not convert the action
into an automatic callback/heal.

## 3. Proposed minimal design (not implemented)

Make the preview distinguish two facts that are currently merged into the
single `prevented` boolean:

- **direct receipt prevented:** Shield of Protection reduces Penance's direct
  HP result to `0 / prevention.allDamage` *after* the hybrid action has landed;
- **callback prevented:** evasion means the Penance callback does not run, so
  neither direct damage nor linked healing happens.

The smallest adapter-only approach is to preserve the existing prevented
primary for Shield of Protection, but allow the Discipline Penance branch in
`_preview_consequences` to calculate same-caster Redemption
`secondaryHealing` consequences when that prevented state specifically means
the post-hit Shield receipt. The existing recipient/range helper remains the
single calculation source. It must retain `certainty: "onHit"`; it must not
present the healing as unconditional or consume randomness.

Suggested implementation boundary:

- **`battle_api/adapter.py`**: replace the overloaded private boolean passed to
  `_preview_consequences` with a narrow, explicit preview context (or a
  narrowly named extra argument) that differentiates `evaded/callback not run`
  from `shield direct receipt blocked`. Use it only for the audited Penance
  branch; keep other skill prevention semantics unchanged.
- **`tests/test_battle_transparency_005_preview.py`**: replace the current
  false no-linked-preview assertion with execution parity coverage described
  below.

No changes are proposed to `heroes/priest.py`, `heroes/hero.py`,
`skills/skill.py`, frontend code, public contracts, database state, RNG
handling, or gameplay rules. The frontend already supports
`secondaryHealing` rows with `onHit`; the data shape does not need expansion.

## 4. Event and receipt ordering

For a landed Penance with a Redemption holder, the live callback orders its
operations as direct `take_damage` first and linked `take_healing` calls
second. Shield of Protection only makes the first receipt a zero-HP result;
it does not alter the subsequent source-code order. The adapter's command
event derivation observes HP mutations and produces typed damage/healing
events from before/after combatant state
([`battle_api/adapter.py`](../../../battle_api/adapter.py#L2818-L2908)).

Expected observable order for the protected, non-evaded case is therefore:

1. normal skill/action event(s);
2. no positive `damageApplied` HP event for the shielded target because its HP
   is unchanged (the existing adapter may expose the immunity semantic through
   its own event/result handling);
3. linked `healingApplied` event(s), or a zero-heal representation when a
   recipient is already full HP, in recipient iteration order.

The proposal only teaches preview to describe the already-live, hit-gated
linked-healing result. It does not modify this order or introduce new events.

## 5. No-mutation and no-RNG guarantees

`BattleAdapter.preview` holds the session lock, validates the revision and
legal command, then evaluates without installing session RNG, executing a
skill, publishing events, or changing revision/turn/command state
([`battle_api/adapter.py`](../../../battle_api/adapter.py#L779-L792)). The
proposed calculation must continue to use the existing finite range helpers,
not `Skill.execute`, `Penance`, `take_damage`, `take_healing`, or random
helpers.

The callback itself has an unused `random.randint(-1, 1)` draw after the
damage receipt, so preview must not attempt a simulated execution merely to
prove this case. Existing `previewUnavailable` handling remains appropriate
for the previously identified ambiguous mixed-buff/legacy-loop state.

## 6. Proposed regression and manual-validation matrix

### Automated tests after approval

1. **Protected, forced hit, one same-caster Redemption holder:** preview has
   primary `prevented`, zero range and `prevention.allDamage`, *and* one
   `secondaryHealing` row with `onHit`; submitted action leaves target HP
   unchanged and emits/records the recipient's healing result.
2. **Protected, forced evasion, same holder:** submitted action leaves both
   target and holder unchanged; preview does not claim an unconditional heal
   and retains hit-gated wording.
3. **Protected, no holder:** primary blocked with no secondary row.
4. **Unprotected, forced hit, multiple holders:** recipient-specific rows stay
   present and remain non-aggregate.
5. **Full-HP holder:** confirm preview reports the healing power/range under
   the established preview policy while live HP remains capped; verify typed
   zero-heal event treatment where the current event contract provides it.
6. **Purity:** deep-compare snapshot, event log, turn/revision, command state,
   Python RNG state and session RNG state before/after preview; patch random
   helpers to fail if called.
7. **Boundary safety:** retain tests for ambiguous mixed records returning
   `previewUnavailable`, stale revision rejection, invalid target/side and
   formation legality.

### Manual checks after approval

Use the browser battle UI in 1v1, 2v2 and 3v3 where the necessary actors are
available:

- hover/focus enemy Penance target with Shield of Protection and a
  same-caster Redemption holder: inspect `Damage 0 / Blocked` and linked
  recipient healing row;
- resolve a non-evaded cast: confirm target HP does not change while the
  Redemption recipient shows the normal healing event/effect;
- force/observe an evaded case: confirm no healing event occurs;
- repeat without Redemption and with an ordinary target; and
- verify hover/focus dismissal, keyboard access, and no UI error.

If reliable evasion forcing is unavailable in browser UI, record that exact
limitation and use the deterministic automated parity test for the branch.

## 7. Risks, ambiguities, and alternatives

### Risks

- A generic interpretation of every prevented action as a callback-running
  action would be wrong: many prevention states occur before or instead of
  downstream effects. The exception must be finite and explicitly confined to
  landed opponent Penance with Shield of Protection.
- The legacy Penance code calculates linked healing from raw attempted damage,
  not actual HP lost. Changing it to zero healing when the shield blocks damage
  would be a mechanics change and is outside this proposal.
- The current event adapter may not publish a direct damage event for zero HP
  loss; the proposal must not fabricate one in preview or UI.

### Alternatives considered

1. **Change live Penance so blocked direct damage suppresses linked healing.**
   Rejected: it changes owner-confirmed live mechanics and is outside a
   transparency correction.
2. **Leave preview silent about linked healing whenever direct damage is
   blocked.** Rejected: it is demonstrably false and conceals a material
   on-hit outcome.
3. **Run Penance in a copied/dry-run battle.** Rejected: it risks side effects
   and RNG consumption/duplication, violating the preview architecture.
4. **Make every secondary row unconditional.** Rejected: evasion prevents the
   callback; `onHit` is the truthful contract.

## Owner decision — rejected

The owner rejected this adapter-only proposal. The clarified design is that
Holy Word Redemption linked healing from opponent-targeted Penance occurs only
when the Penance hit causes valid direct damage to its target. Shield of
Protection remains `Damage 0 · Blocked` and causes no linked healing; evasion
also causes no linked healing. The live callback behaviour described here is a
combat-mechanics defect, not a preview-only discrepancy.
