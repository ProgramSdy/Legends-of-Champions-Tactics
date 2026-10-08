# BATTLE-TRANSPARENCY-005 — Penance Valid Direct Damage Proposal

**Date:** 2026-10-08  
**Status:** Owner-review only — do not implement until explicitly approved.  
**Supersedes:** The rejected adapter-only proposal in
[`2026-10-08_BATTLE-TRANSPARENCY-005_Penance_Shield_of_Protection_Proposal.md`](2026-10-08_BATTLE-TRANSPARENCY-005_Penance_Shield_of_Protection_Proposal.md).  
**Scope:** Priest Discipline's opponent-targeted Penance and only its
same-caster Holy Word Redemption linked healing. This is a mechanics and
truthful-preview proposal; it does not authorise a broader damage-receipt
refactor, status redesign, or UI work.

## Owner-confirmed rule

Holy Word Redemption linked healing after opponent-targeted Penance occurs
only if the landed Penance causes **valid direct damage to its selected
target**. The authoritative definition is a positive selected-target HP loss
after that target's live `take_damage` receipt resolves:

```text
valid_direct_damage = target.hp_after_receipt < target.hp_before_receipt
```

Raw attempted damage, a non-evaded cast, a damage-log string, a status change,
or damage redirected to another combatant do not satisfy this rule by
themselves. This deliberately uses existing engine state, not a copied adapter
or React formula.

## 1. Live-path findings and root cause

`Skill.execute` handles a `damage_healing` opponent target by calling
`evasion_check`. On evasion it returns before the Penance callback; only a
non-evaded target enters the callback
([`skills/skill.py`](../../../skills/skill.py#L323-L340)).

The current Penance callback computes raw 17–21 damage, calls the target's
authoritative `take_damage`, then unconditionally heals every same-caster
Holy Word Redemption holder
([`heroes/priest.py`](../../../heroes/priest.py#L529-L556)). It uses raw
attempted damage to calculate the linked amount and never tests whether
`take_damage` reduced the selected target's HP.

Shield of Protection is resolved in `Hero.take_damage_action`: it returns
without reducing the target's HP
([`heroes/hero.py`](../../../heroes/hero.py#L855-L871)). The callback still
continues to linked healing. That is the owner-confirmed combat-mechanics bug.

The current preview identifies Shield as `prevention.allDamage` and reports
`Damage 0 · Blocked`
([`battle_api/adapter.py`](../../../battle_api/adapter.py#L2058-L2100)).
Its present omission of linked-healing rows matches the intended user result,
but only because live combat is currently inconsistent with it.

## 2. Relevant direct-damage boundaries

| Boundary | Current engine path | Selected target HP loss? | Required linked Redemption result |
| --- | --- | --- | --- |
| Evasion | Dispatcher returns before callback. | No. | No linked healing. |
| Shield of Protection | Receipt returns immunity. | No. | No linked healing. |
| Holy Word Shell fully absorbs | Receipt reduces Shell only. | No. | No linked healing. |
| Holy Word Shell partially absorbs | Receipt reduces target by remainder. | Yes. | Linked healing occurs. |
| Ordinary receipt | Receipt reduces target. | Yes. | Linked healing occurs. |
| Void Connection / shared receipt | Use selected target's post-receipt HP, never another hero's loss. | Only if selected target loses HP. | Gate solely on selected target loss. |
| Any current/future zero receipt | No selected target HP reduction. | No. | No linked healing. |

Penance is `ranged_instant`, currently a 1.0 formation multiplier, but the
predicate must remain receipt-based so future receipt logic cannot recreate the
bug ([`heroes/hero.py`](../../../heroes/hero.py#L701-L718)).

Adapter `damageApplied` events are derived from before/after HP, and are
therefore evidence of a positive loss. They are emitted after engine execution,
however, so they must not become the gameplay predicate
([`battle_api/adapter.py`](../../../battle_api/adapter.py#L2818-L2908)).

## 3. Minimal proposed engine correction

Make one Penance-local change in `Priest_Discipline.penance`:

1. immediately before `other_hero.take_damage`, capture selected-target
   `hp_before_receipt`;
2. invoke the existing authoritative `take_damage` unchanged;
3. calculate `valid_direct_damage` from selected target post-receipt HP; and
4. execute the existing same-caster Redemption holder/healing loop only when
   that result is true.

The existing evasion, raw damage roll, formation modifier, Shield/Shell/shared
receipt, same-caster holder discovery, linked-healing formula, healing
modifiers, full-HP cap, valid-hit RNG order, and ally iteration order remain
unchanged. No change is proposed to `Hero.take_damage`'s legacy string return.

This is intentionally not a global damage-receipt refactor. A new structured
receipt API is higher-risk because many legacy callers consume the current
behaviour; selected target HP already gives the exact owner-approved predicate.

### Required live event/order semantics

For opponent Penance:

1. evasion occurs before callback entry;
2. non-evaded Penance resolves selected-target `take_damage`;
3. only positive selected-target HP loss enables each existing linked
   `take_healing`, in current ally iteration order;
4. the adapter derives target `damageApplied` before those
   `healingApplied` events.

Shielded or fully Shell-absorbed Penance has no step 3. No synthetic damage or
healing event should be added.

## 4. Preview alignment after engine approval

The current Shield preview remains correct:

```json
{
  "primary": {
    "kind": "prevented",
    "amountRange": { "min": 0, "max": 0 },
    "reasonId": "prevention.allDamage"
  },
  "consequences": []
}
```

After the engine repair, preview aligns as follows:

- **Shield:** retain the blocked primary and no `secondaryHealing` row.
- **Guaranteed full Shell absorption:** no valid direct damage and no linked
  row when current Shell absorption covers the whole audited Penance range.
- **Possible partial Shell receipt:** never claim an unconditional linked heal.
  If the finite preview cannot express the receipt-dependent result truthfully,
  return existing revision-bound `previewUnavailable` for that narrow state;
  do not dry-run the engine or show false precision.
- **Normal opponent Penance:** retain recipient-specific
  `secondaryHealing` with `certainty: "onHit"`, now meaning a non-evaded
  action that also produces positive selected-target HP loss.
- **Evasion:** remains represented by direct Hit Chance; it never produces an
  `always` linked-healing claim.

React requires no formula or layout change for Shield. The adapter remains the
sole preview authority. If implementation uses the narrow Shell-unavailable
policy, the existing unavailable UI is sufficient.

## 5. No-mutation and no-RNG guarantees

The engine repair must not add RNG. Its zero-receipt path should skip the
linked-healing block, including its current unused variation draw, because
linked healing is no longer occurring. This is an intentional seed-trace
change caused by the mechanics correction and must be tested.

`BattleAdapter.preview` must retain its current purity boundary: it validates
under the session lock, but does not install session RNG, execute skills,
mutate HP/status, publish events, or alter revision/turn/commands
([`battle_api/adapter.py`](../../../battle_api/adapter.py#L779-L792)).
Preview must inspect finite current state only; it must not dry-run Penance or
`take_damage`.

## 6. Proposed regression and manual-validation matrix

### Engine / adapter tests after approval

1. Shield, forced non-evasion, same-caster Redemption holder: target HP stays
   unchanged, holder HP stays unchanged, no linked `healingApplied` event,
   and preview is blocked with no secondary row.
2. Shield, forced evasion: no target/holder HP change and no callback-side
   mutation.
3. Shield, no holder: retain blocked result and no healing.
4. Normal target, forced non-evasion, one and multiple same-caster holders:
   target loses HP and each holder heals once in existing iteration order;
   preview has recipient-specific `onHit` rows.
5. Fully absorbing Shell: no target HP loss and no linked healing; cover raw
   damage equal to, below, and above the absorption boundary.
6. Partially absorbing Shell: target loses HP and linked healing occurs; assert
   receipt/event order.
7. Shared/void-receipt case: selected target HP, not any linked hero's HP,
   decides linked healing.
8. Full-HP Redemption holder: valid direct damage still invokes `take_healing`
   and retains current zero-heal event semantics.
9. Preview purity: deep-compare state, events/log, turn/revision, global RNG
   and session RNG; patch random helpers to fail if preview calls them.
10. Preserve stale, unavailable/cooldown, wrong-side, dead, duplicate,
    cardinality, and rear-target legality coverage.

### Manual browser checks after approval

Validate 1v1, 2v2 and 3v3 where state permits:

- shielded enemy plus same-caster Redemption holder: blocked preview, no linked
  recipient row, no healing animation/HP update after a non-evaded cast;
- unshielded damage: target damage followed by linked holder healing;
- fully/partially absorbed Shell;
- evasion; one/multiple/full-HP holders; and
- hover/focus dismissal, keyboard selection, and console/UI errors.

Record any branch that cannot be reliably produced in browser UI and use the
deterministic engine proof for that branch.

## 7. Contract/UI impact

For definite Shield behaviour, no API response shape, endpoint, model, or UI
layout changes are needed: the engine will be made consistent with the already
truthful blocked preview. Existing `secondaryHealing.certainty: "onHit"`
remains adequate for normal Penance.

If the approved implementation chooses the conservative ambiguous-Shell
`previewUnavailable` outcome, it uses an existing response variant. Only
after implementation should relevant contract/API/architecture documentation
be updated to define the exact receipt condition and any unavailable boundary.
No contract or UI documentation is changed by this proposal.

## 8. Risks and alternatives

- **Wrong predicate:** raw attempted damage repeats the Shield/Shell bug;
  generic event inspection is too late and couples mechanics to presentation.
- **Broad change:** a global `take_damage` receipt object risks many legacy
  callers; keep this Penance-local unless separately approved.
- **Seed changes:** zero-receipt actions no longer consume a former
  linked-healing variation draw; document deterministic trace changes.
- **Legacy special receipts:** use tests to establish target-HP semantics rather
  than relying on return prose.

Rejected/deferred alternatives:

1. Adapter-only suppression: rejected by owner because it masks the mechanics
   bug.
2. Raw-damage gating: rejected because blocked/fully absorbed attacks heal.
3. Return-string parsing: rejected because prose is not an authoritative
   receipt.
4. Immediate global structured receipt API: deferred as disproportionate.
5. Full Shell-range UI modelling now: defer; prefer narrow
   `previewUnavailable` over fake precision.

## Owner decision requested

Approve or reject the Penance-local engine correction and the corresponding
finite preview alignment. No code or tests should be changed until approval is
explicit.

