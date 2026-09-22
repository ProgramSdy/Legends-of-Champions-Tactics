# BATTLE-TRANSPARENCY-004 — Paladin Holy and Protection Engine Audit

**Date:** 2026-09-18  
**State:** Pre-implementation audit complete  
**Scope:** The six player-selectable active skills of published Paladin Holy and
Protection only. No live mechanic, balance, or status lifecycle change is
authorised by this audit.

## Role Dispatch and Ownership

All five required roles were dispatched before implementation:

- **project-manager** (`/root/btt004_pm`) — scope sequencing, risks,
  documentation/completion gates.
- **game-engine-developer** (`/root/btt004_engine`) — six live skill paths,
  adapter boundary, pure-range and no-mutation/RNG audit.
- **ui-developer** (`/root/btt004_ui`) — existing typed preview, self-preview,
  accessibility, draft/full, and runtime-parser audit.
- **test-automator** (`/root/btt004_test`) — deterministic engine/API/UI and
  browser validation matrix.
- **reviewer** (`/root/btt004_reviewer`) — independent pre-code mechanics and
  contract review.

All five roles completed read-only audits without editing implementation files.

## Published Scope and Target Shapes

| Hero | Skill ID | Live target shape | Preview boundary |
| --- | --- | --- | --- |
| Protection | `skill.paladin.hammer_of_revenge` | one living enemy; ranged instant | target card |
| Protection | `skill.paladin.shield_of_righteous` | one living enemy; melee/front screened | target card + actor buff fact |
| Protection | `skill.paladin.heroric_charge` | one living enemy; ranged instant/control | target card + actor branch facts |
| Holy | `skill.paladin.purify_healing` | one living ally, including caster | healing target card |
| Holy | `skill.paladin.holy_blast` | two living enemies for command | one-target draft / ordered complete pair |
| Holy | `skill.paladin.shield_of_protection` | targetless, exact `targetIds: []` | existing `selfPreview` |

`skill.paladin.holy_aura` is passive and must remain absent from the finite
allowlist, preview endpoint success path, UI preview requests, and tests that
describe player-selectable preview coverage.

## Shared Authoritative Rules

- Preview remains held under the battle-session lock, revision-bound, and
  validates current actor, available audited skill, liveness, side, duplicates,
  cardinality, and targetless shape.
- It must not call `Skill.execute`, `resolve_targets`, an action or independent
  action callback, `StatusDispell`, status manager, damage/healing mutation, or
  any random helper. It must leave engine state, session RNG, process RNG,
  events/log, cursor, turn, and revision unchanged for accepted and rejected
  requests.
- Damage Hit Chance is the existing evasion-only fact. Existing pure formation
  and damage-receipt helpers remain the source of direct ranges; healing range
  remains post-modifier power before the live maximum-HP cap.
- The preview must use finite typed facts. React must not recreate combat,
  dispel, stack, target, or RNG rules.

## Six Live Paths

### Hammer of Revenge

- Raw direct range is `max(actor.damage + [-4,-1] - target.defense, 0)` plus a
  self-debuff band: zero debuffs `+0`, one `+3..5`, two `+6..8`, three or more
  `+9..11`.
- The live count intersects only magic, bleeding, disease, and physical status
  lists. Toxic is deliberately excluded despite broader legacy AI counting.
- Ranged-instant has no formation penalty, then normal audited receipt applies.
- If the actor has Shield of Righteous, the target lacks Hammer of Revenge, and
  the action lands, it applies a 3-round target damage reduction based on
  `round(target.original_damage * .2)`. An existing Hammer status is not
  refreshed or increased. That fact is on-hit/first-application only.

### Shield of Righteous

- Direct raw range is 18–22, defence-ignoring, then melee formation/receipt.
  A living front enemy screens rear targets.
- The actor defence effect is effectively always attempted: normal execution
  applies it on hit and the inherited independent path applies it on evade,
  all-damage immunity, dead/no-hit paths.
- It adds `ceil(original_defense * .15)` at first application and next stack,
  caps at two stacks, and refreshes duration to three rounds at cap. Preview
  must report first/next-stack/refresh, never falsely label it `onHit`.

### Heroric Charge

- Direct raw range is `max(1, round(actor.damage - target.defense) + [-1,1])`,
  then ranged-instant receipt.
- Ordinary non-control-immune hit: Scoff, optional casting interrupt, self heal
  28–32, cooldown 3, and direct damage.
- Evasion/all-damage-immunity/dead/no-hit path: independent callback self heal
  20–24 and cooldown 3, with no Scoff/interrupt/damage.
- Warlust control immunity suppresses Scoff but does **not** suppress direct
  damage; legacy execution can still interrupt a casting target, then uses the
  independent 20–24 heal/cooldown path. All-damage immunity takes precedence.
- Same-source Scoff refresh has a legacy duplicate-record defect. Preview must
  not claim a clean refresh in that ambiguous state; omit/unavailable is safer.

### Purify Healing

- Healing raw range is 23–27, then target healing modifiers; it never has Hit
  Chance. Its own buff has duration two and can first-apply or refresh only a
  matching same-source Buff. A target status active under another source can
  be neither applied nor refreshed; do not describe that as refresh.
- Eligible candidates are active bleeding, disease, and toxic statuses only;
  magic and physical statuses are excluded. Live code shuffles candidates and
  gives exactly one to `StatusDispell`.
- A single proven supported candidate may be named. With multiple candidates,
  never predict one status: use a finite uncertainty fact such as “attempts one
  eligible status (random), may remove none.” Some list members have no
  dispeller branch. `unstable_compound` is unsafe for preview because its
  dispeller path consumes RNG and can damage; return unavailable/omit a removal
  fact rather than simulating it.

### Holy Blast

- One invocation uses one shared raw roll 20–25. The first **successful hit**
  gets the full band; later successful hits get `ceil(2/3 * raw)` (14–17), then
  each target gets normal ranged-projectile formation/receipt.
- Target order means post-resolution hit order, not selected slot order. If
  selected target one evades/is immune and selected target two lands, target
  two is full (20–25), not reduced. A complete pair must use a truthful union
  / conditional fact or unavailable result for that dependent second-target
  case; it cannot promise 14–17 unconditionally.
- Preview may accept a one-target draft and then an ordered distinct pair. The
  real command retains exact live target cardinality and no aggregate total.

### Shield of Protection

- Exact targetless request, using BTT-003 `selfPreview`—never a fake target.
- Live action attempts all active magic, bleeding, disease, and physical
  statuses, excluding toxic; it then first-applies or refreshes all-damage
  immunity for two rounds and applies cooldown 3.
- List only removals that `StatusDispell` can actually complete with required
  live records; category membership alone is insufficient. Never call the
  dispeller in preview, including its random `curse_of_agony` branch, and never
  forecast a later blocked attack.

## Legacy Boundaries That Preview Must Mirror, Not Repair

- `Hero.list_status_debuff_magic` is missing a comma, producing runtime key
  `stitch_of_agonyshadow_word_insanity`; neither separate status is eligible
  where live code consumes that list.
- Several category-listed statuses have no `StatusDispell` handler or require a
  matching Buff/Debuff record. The preview must inspect the actual live
  eligibility/record boundary without invoking dispel code.
- No approval exists to normalise Heroric Charge heal branches, same-source
  Scoff duplication, Purify no-op selection, or Holy Blast post-evasion target
  order.

## Contract and Test Direction

- Add exactly the six active IDs to the finite audited allowlist; leave Holy
  Aura and generic Paladin fallbacks unsupported.
- Reuse `selfPreview` for Shield of Protection. Holy Blast joins the existing
  finite preview-only draft allowlist, preserving real cardinality.
- New typed facts must cover only audited Paladin needs: revenge damage band,
  first-only Hammer reduction, defence first/stack/refresh, branch-safe Charge
  facts, Purify uncertainty, and damage immunity. Existing cooldown, interrupt,
  Scoff, healing, and status-removal facts are reused only when truthful.
- Test every skill plus stale/wrong actor/unavailable/passive/duplicate/
  illegal/dead/cardinality rejection; deep state plus both RNG sources;
  monkeypatched random helpers; same-seed command equivalence; 1v1/2v2/3v3
  formation, draft/full, stacks/caps, immunity/control, and dispeller
  boundaries. Browser validation must state any inability to seed legacy states.

## Implementation Decision

No owner direction is currently required: the task can proceed with
conservative finite data, branch-aware ranges, and omitted/unavailable rows
where live code is ambiguous. Any demand to guarantee a Purify removal,
normalise Heroric Charge, or make Holy Blast slot two always reduced would be a
mechanic change and requires owner approval.
