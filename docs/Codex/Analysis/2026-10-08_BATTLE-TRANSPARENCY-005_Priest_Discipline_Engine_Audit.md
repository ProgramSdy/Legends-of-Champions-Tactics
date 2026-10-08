# BATTLE-TRANSPARENCY-005 — Priest Discipline Engine Audit

**Date:** 2026-10-08  
**Scope:** Pre-confirmation facts for `hero.priest.discipline` only. This is a
read-only audit, not a mechanic, balance, or status-lifecycle change.

## Five-role dispatch gate

The required roles were dispatched before implementation, in a staged sequence
because this workspace permits three child agents while the root agent remains
active:

| Role | Ownership | Contribution at audit gate |
| --- | --- | --- |
| Project manager | Scope, sequencing, validation and documentation gates | `/root/btt005_pm` recorded the cardinality and extra-recipient gates. |
| Engine | Live mechanics, adapter/API and purity | `/root/btt005_engine` completed the read-only source audit. |
| UI | Types, compact presentation and interaction compatibility | `/root/btt005_ui` dispatched for the frontend boundary audit. |
| Test | Deterministic hybrid/status/purity matrix | `/root/ui027_test` completed the BTT-005 test study. |
| Reviewer | Independent mechanics/contract gate | `/root/ui027_review` conditionally approved the source audit. |

No production implementation was started before this record. Existing dirty
UI-027 work and the unrelated Paladin Holy artwork/scale adjustment are outside
this task and must remain untouched.

## Authoritative live definitions and target authority

`Priest_Discipline` registers Penance as single-target `damage_healing` with
`ranged_instant`, Holy Word Redemption as single-target `buffs`, and Holy Word
Punishment as two-target `damage` with `ranged_instant`
([`heroes/priest.py`](../../../heroes/priest.py#L509-L518)). Stable public IDs
already exist in [`battle_api/adapter.py`](../../../battle_api/adapter.py#L128-L132).

The adapter's legal-target authority chooses living allies for healing/buffs,
both living sides for `damage_healing`, and living opponents for damage; only
melee is formation-screened. Therefore Penance may lawfully target either
side and both direct-damage Discipline actions may target a legal rear hero.
[`_legal_actions`](../../../battle_api/adapter.py#L2960-L3005) publishes
`min(skill.target_qty, len(valid_targets))`, which is the live command
authority.

## Audited immediate facts

### Penance

- **Ally branch:** the callback rolls 21–25 raw healing and calls
  `take_healing`; recipient modifiers and full-HP caps apply. It has no
  evasion, hit chance, formation multiplier, or immediate Redemption trigger
  ([`heroes/priest.py`](../../../heroes/priest.py#L520-L527)).
- **Opponent branch:** hybrid `Skill.execute` performs evasion before calling
  the callback. On hit it rolls 17–21 raw damage, deliberately ignores
  defence/resistance, and sends `ranged_instant` to `take_damage`
  ([`skills/skill.py`](../../../skills/skill.py#L323-L340),
  [`heroes/priest.py`](../../../heroes/priest.py#L529-L556)). Ranged instant
  has a 1.0 position multiplier. Shell/linked receipt remains HP-facing, but
  normal damage-immunity resolution is *not* part of this hybrid path.
- A landed enemy Penance heals every living ally with a same-caster Redemption
  record. The raw linked amount is `round(0.7 × raw damage)` before recipient
  healing receipt, is recipient-specific, and is `onHit` even if absorption
  means no HP was lost. The callback makes an unused `randint(-1, 1)` draw;
  preview must neither reproduce nor consume it
  ([`heroes/priest.py`](../../../heroes/priest.py#L535-L553)).

### Holy Word Redemption

First application creates or recycles a same-caster buff with duration 5 and
effect 0.7; a same-caster refresh sets duration 5
([`heroes/priest.py`](../../../heroes/priest.py#L609-L631)). It has no
immediate healing. Later same-caster landed enemy Penance/Punishment actions
and later Punishment ticks may heal its holder, but no future amount is safe to
promise in a preview. The status manager decrements/removes its real record
at round updates ([`game/status_effect_manager.py`](../../../game/status_effect_manager.py#L338-L349)).

There are two material legacy boundaries:

1. At caster HP at or below 75% with more than one ally, `Skill.execute`
   immediately applies Redemption to the selected target and can select an
   additional target; its all-protected fallback uses `random.choice`
   ([`skills/skill.py`](../../../skills/skill.py#L345-L377)).
2. The target's boolean status is global. If it is active only from another
   Discipline caster, the callback's apparent refresh prose can leave no
   same-caster record changed ([`heroes/priest.py`](../../../heroes/priest.py#L627-L631)).

**Approved safe preview policy:** for either boundary, return the ordinary
revision-bound `previewUnavailable` representation rather than guess an extra
recipient, call random, or claim an application/refresh that the live state
cannot prove. This does not block the legal command.

### Holy Word Punishment

The callback draws one shared 7–11 direct-damage roll for all selected targets.
For each landed target it first adds a same-caster status only when the target's
global Punishment flag is inactive, then applies direct damage. An existing
flag still permits direct damage but is not refreshed
([`heroes/priest.py`](../../../heroes/priest.py#L558-L590)). A fresh record is
duration 4; preview may describe only the finite immediate `apply` versus
`alreadyActive` boundary, not the future stored effect.

Each landed selected target then triggers healing once per living same-caster
Redemption holder. This healing has a recipient-specific random range and a
coefficient based on the number of linked recipients
([`heroes/priest.py`](../../../heroes/priest.py#L592-L604)); it is `onHit`,
not an aggregate or an unconditional heal. Future Punishment tick damage and
its linked healing occur in the status manager with separate RNG and are
excluded from preview ([`game/status_effect_manager.py`](../../../game/status_effect_manager.py#L351-L377)).

## Live cardinality decision

The owner-approved wording says two selected opponents, while live legal
authority publishes **one** required target when only one living opponent
exists (notably 1v1 or a sole survivor). BTT-005 must preserve that authority:

- with published maximum two, one target is a draft preview and two distinct
  targets are the complete command;
- with published maximum one, one target is already the complete lawful
  command;
- preview never requires more targets than the published action or relaxes a
  published two-target command.

This is a documented legacy compatibility decision, not a rule change.

## Preview architecture and implementation constraints

`BattleAdapter.preview` already holds the session lock, validates revision,
current player-command actor, available/published skill, target IDs, liveness,
duplicates and target count, then evaluates without installing session RNG,
executing skills, or publishing events
([`battle_api/adapter.py`](../../../battle_api/adapter.py#L779-L892)). The
generic evaluator currently identifies healing only through `skill_type ==
"healing"`, so Penance needs an adapter-owned selected-side branch; React must
not choose it. The current finite backend and frontend allowlists omit all
Discipline skills ([`battle_api/adapter.py`](../../../battle_api/adapter.py#L809-L843),
[`useBattlePreview.ts`](../../../web-ui/lib/battle/useBattlePreview.ts#L6-L47)).

Implementation may add only small pure primitives that enumerate audited
ranges. It must not call `Skill.execute`, a callback, target resolution, status
updates, or any random helper. Typed consequences must stay finite. Existing
`secondaryHealing` is structurally suitable for recipient ranges, but the UI
must label linked allies rather than use its current self-healing wording.

## Required proof matrix

Tests must cover 1v1/2v2/3v3; both Penance sides; rear legal targeting;
evasion, receipt, full HP, all-damage/absorption behavior where live; same-
caster linked recipients; Redemption application/refresh/other-source and
low-HP extra-recipient boundaries; Punishment one-target complete, two-target
draft/full, duplicate/dead/wrong-side/stale rejection, apply/already-active,
and no future tick totals. Accepted and rejected previews must deep-compare
combat state, records, events/logs, turn/revision and both RNG states; patched
random helpers must fail if called; same-seed commands after preview must equal
untouched controls.

## Reviewer gate

The independent reviewer conditionally approved implementation only with the
safe unavailable policy above, source-aware status boundaries, hit-gated linked
recipient facts, and the published-cardinality rule. No gameplay mechanic,
formula, cooldown, target rule, progression, or generic preview fallback is
authorised by this audit.
