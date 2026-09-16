# BATTLE-TRANSPARENCY-003 Warrior Engine Audit

**Date:** 2026-09-16  
**Scope:** Audit only; no gameplay, API, or UI implementation change  
**Published definitions:** `hero.warrior.defence`,
`hero.warrior.weapon_master`, `hero.warrior.berserker`

## Authority path inspected

The nine published actions are defined in `heroes/warrior.py` and enter the
live battle through the adapter's published legal actions and command
validation (`battle_api/adapter.py:2032-2085`, `1080-1123`). The adapter turns a
zero-target action into the engine's legacy `['none']` sentinel and otherwise
passes a single object or list into `Skill.execute`
(`battle_api/adapter.py:1176-1184`). `Skill.execute` performs death, evasion,
all-damage, damage-nature, and control-immunity classification before invoking
the action (`skills/skill.py:115-166`, `178-317`). Final formation damage is
applied exactly once by `Hero.take_damage_calculation`
(`heroes/hero.py:701-718`), followed by absorption/linked-damage receipt
(`heroes/hero.py:736-872`).

Preview must therefore remain a locked, read-only sibling of command
validation. The existing boundary already checks revision, current actor,
player-command ownership, skill availability, published action, target count,
duplicates, and legal IDs (`battle_api/adapter.py:674-766`) without installing
session RNG or calling `Skill.execute` (`battle_api/adapter.py:677-685`).

## Shared targeting, hit, prevention, and receipt facts

- `Devastate`, `Shield Bash`, `Fatal Strike`, `Armor Crush`, and `Strike of
  Meteorite` are melee. While any living enemy front hero exists, rear heroes
  are not legal targets (`battle_api/adapter.py:2079-2085`). A rear attacker's
  final melee damage is floored after a `0.7` multiplier
  (`heroes/hero.py:710-718`).
- `Thunder Pot` is ranged projectile and `Moon Slash` is ranged instant
  (`heroes/warrior.py:227-229`, `864-867`). Both can target any living enemy.
  Projectile damage is floored after `0.60` for rear-to-rear and `0.80` for
  mixed front/rear positions; ranged instant receives no formation modifier
  (`heroes/hero.py:713-718`).
- Every Warrior damage action passes the same direct evasion roll before the
  action. Evasion is `ceil(max-derived evasion)` with the live cap logic at
  `skills/skill.py:100-107`; the existing preview inverse is at
  `battle_api/adapter.py:768-775`.
- All nine Warrior damage skills leave `damage_nature='NA'`. Consequently the
  physical/magical branches in `Skill.resolve_targets` do not classify them as
  physical or magical (`skills/skill.py:139-159`), even though Warrior's
  `hero_damage_type` is physical (`heroes/warrior.py:15-21`). All-damage
  immunity still prevents them before their action runs
  (`skills/skill.py:127-138`). Preview must mirror this live classification,
  not infer physical immunity from faculty.
- `Thunder Pot` alone is declared `is_control_skill=True`
  (`heroes/warrior.py:229`). Warlust therefore prevents the whole Thunder Pot
  hit, including its direct damage, at target resolution. `Shield Bash` and
  `Strike of Meteorite` are not declared control skills, so Warlust does not
  prevent their stun/interruption/Armor Breaker live paths.
- Holy Word Shell absorption and Void Connection's recipient share are
  deterministic receipt facts already mirrored by
  `_apply_audited_damage_receipt` (`battle_api/adapter.py:793-812`). The preview
  must apply formula, formation, and receipt once each, in that order.
- A landed hit can display `0` direct HP damage after formation flooring,
  absorption, or linked receipt while still applying its material status. Do
  not use positive damage as the definition of a hit.

## Exact action audit

### Warrior Defence

#### Devastate

- **Target:** one legal melee enemy (`heroes/warrior.py:227`).
- **Raw direct damage:** for each integer `v` in `[-1, 1]`,
  `max(ceil((actor.damage + v - target.defense) * 0.75), 1)`
  (`heroes/warrior.py:253-257`). Apply melee formation and audited receipt
  afterward.
- **Armor Breaker:** the effect occurs on an accepted hit before damage
  receipt. No current Armor Breaker becomes stack 1; exactly stack 1 becomes
  stack 2; stack 2 or greater only refreshes duration. Each new stack reduces
  current defence by `ceil(original_defense * 0.15)` and accumulates the amount
  restored later. Every application/stack/refresh sets duration to 2
  (`heroes/warrior.py:258-280`). The round status phase decrements the duration
  and restores all accumulated defence when it reaches zero
  (`game/status_effect_manager.py:177-186`).
- **Cooldown/control:** no cooldown; no interrupt or control result.

#### Shield Bash

- **Target:** one legal melee enemy (`heroes/warrior.py:228`).
- **Raw direct damage:** for each integer `v` in `[-2, 2]`,
  `max(int((actor.damage + v - target.defense) / 4), 1)`
  (`heroes/warrior.py:247-251`). Python `int` truncation is part of the live
  formula. Apply melee formation and receipt afterward.
- **Stun/interruption:** on every accepted hit, `stunned=True` and
  `stun_duration += 1`; active magic casting is also interrupted
  (`heroes/warrior.py:231-242`). This includes hits whose received HP damage is
  zero. Stun consumes one turn while duration is positive, and is cleared only
  on a later status pass after duration is already zero
  (`game/status_effect_manager.py:157-164`, `heroes/hero.py:1394-1406`).
- **Cooldown:** every accepted hit sets cooldown 3
  (`heroes/warrior.py:243-246`). A miss or immunity also sets cooldown 3 via
  the generic special-name path (`skills/skill.py:299-308`). Cooldowns
  decrement at the start of rounds and become available on a subsequent pass
  after reaching zero (`game/game.py:207-216`).
- **Control immunity caveat:** `Shield Bash` is not marked as a control skill,
  so Warlust does not prevent its live stun. Preview must not claim otherwise.

#### Thunder Pot

- **Target:** ranged-projectile multi-target action with nominal quantity 2;
  the adapter requires `min(2, living legal enemies)` for the real command
  (`heroes/warrior.py:229`, `battle_api/adapter.py:2053-2066`).
- **Raw direct damage, per hit target:** let
  `base = round((actor.damage - target.defense) / 3)`. For each integer `v` in
  `[-1, 1]`, raw damage is `max(1, base + v)`
  (`heroes/warrior.py:301-305`). Apply ranged-projectile formation and receipt
  afterward. The variation is rolled separately for each hit target.
- **Scoff/interruption:** a non-control-immune hit applies/replaces Scoff from
  the actor with a named debuff duration 1, and interrupts active magic
  casting (`heroes/warrior.py:307-359`). Scoff forces an automatic damage
  action toward its living source and is consumed by that action
  (`heroes/hero.py:1424-1450`, `1264-1300`). A Warlust target is classified as
  control-immune before the normal action receives it
  (`skills/skill.py:153-159`).
- **Self effect/cooldown:** a normal skill-action invocation adds 45 fire,
  frost, death, and nature resistance, records Shield Lash, and sets Thunder
  Pot cooldown 3 (`heroes/warrior.py:282-296`). The visible Shield Lash record
  uses duration 2 and the status manager removes the four stored boosts when
  it expires (`heroes/warrior.py:336-349`,
  `game/status_effect_manager.py:926-949`). A complete miss/immunity sets
  cooldown 3 but does not invoke the independent self effect
  (`skills/skill.py:209-242`).
- **Material implementation ambiguity:** in a partial hit plus control-immune
  pair, generic multi-target dispatch invokes Thunder Pot once for the immune
  target and again for the hit list (`skills/skill.py:261-271`). The method
  applies the self resistance at the top of every invocation, so this path can
  add 90 while the bookkeeping dictionary retains only 45. In addition, its
  per-target loop can add duplicate Shield Lash buff records
  (`heroes/warrior.py:282-349`). This can leave resistance/buff lifecycle state
  inconsistent. The attached `independent_effect_action` is not called by the
  multi-target miss branch. This is a live-rule defect/ambiguity and must be
  escalated; preview must not silently normalize it.

### Warrior Weapon Master

#### Fatal Strike

- **Target:** one legal melee enemy (`heroes/warrior.py:529`).
- **Raw direct damage:** for each integer `v` in `[-3, 3]`,
  `max(actor.damage + v - target.defense, 1)`
  (`heroes/warrior.py:533-537`). Apply melee formation and receipt afterward.
- **Healing reduction:** on the first accepted application only, live healing
  uses `healing_reduction_effects['fatal_strike'] = 0.7`, i.e. 70 percentage
  points in the additive healing-reduction calculation
  (`heroes/warrior.py:538-557`, `heroes/hero.py:881-890`). The named debuff
  lasts 2 and removes that modifier on expiry
  (`game/status_effect_manager.py:951-964`). Re-hitting while the status is
  active neither stacks nor refreshes duration (`heroes/warrior.py:558-560`).
- **Ambiguity:** the named Debuff's unused `effect` is `0.8`, while actual
  healing reduction is `0.7` (`heroes/warrior.py:540`, `549-555`). Preview must
  report the effective live 70%, not the record's 0.8, and documentation should
  record the mismatch.
- **Cooldown/control:** no cooldown or control.

#### Armor Crush

- **Target:** one legal melee enemy (`heroes/warrior.py:530`).
- **Raw direct damage by pre-action Armor Breaker state**, for every integer
  `v` in `[-3, 3]` and `actual = actor.damage + v`:
  - absent: `max(ceil((actual - target.defense) * 0.55), 1)`;
  - current stack 1: multiplier `0.65`;
  - current stack 2 or greater: multiplier `0.75`.
  These use defence before this action's new reduction
  (`heroes/warrior.py:562-612`). Apply melee formation and receipt afterward.
- **Armor Breaker:** absent becomes stack 1; stack 1 becomes 2; stack 2 becomes
  3; stack 3+ refreshes only. Each new stack reduces defence by
  `ceil(original_defense * 0.15)`; duration is 2
  (`heroes/warrior.py:569-611`).
- **Wound boundary:** transition from pre-action stack 1 to 2 applies
  `wound_armor_crush` for duration 2 and immediately reduces agility by
  `int(current_agility * 0.2)` (`heroes/warrior.py:569-584`). Expiry restores
  the stored amount (`game/status_effect_manager.py:977-985`).
- **Bleed boundary:** transition from pre-action stack 2 to 3 applies
  `bleeding_armor_crush` for duration 3 and records a later tick base of 8-12
  (`heroes/warrior.py:585-597`). The future tick is separately randomized and
  is explicitly not a preview total (`game/status_effect_manager.py:966-975`).
- **Cooldown/control:** no cooldown or control.

#### Antivenom Potion

- **Target:** targetless self action: `target_qty=0`; published command uses an
  empty target list and the engine sentinel (`heroes/warrior.py:531`,
  `battle_api/adapter.py:2070-2072`, `1176-1184`).
- **Immediate healing:** raw discrete values 18, 19, and 20, then the actor's
  additive healing boosts/reductions and rounding, then HP cap
  (`heroes/warrior.py:614-620`, `heroes/hero.py:881-890`). The established
  preview convention reports modified healing power before HP cap.
- **Self buff:** immediately adds 45 poison resistance, sets Antivenom Potion,
  and adds a duration-2 named buff (`heroes/warrior.py:615-640`). Expiry removes
  the stored 45 (`game/status_effect_manager.py:987-1001`). Cooldown is 3
  (`heroes/warrior.py:622-625`).
- **Removal set:** the action passes every currently active status in the union
  of `list_status_debuff_bleeding` and `list_status_debuff_toxic` to the legacy
  dispeller before healing (`heroes/warrior.py:642-650`; category lists at
  `heroes/hero.py:135-137`). The dispeller actually implements Poisoned Dagger,
  Moon Slash bleed, Sharp Blade bleed, Crimson Cleave bleed, Wound Backstab,
  Paralyze Blade, Mixed Venom, Acid Bomb, and Armor Crush bleed
  (`game/status_dispell.py:32-37`, `74-95`, `210-215`, `252-277`, `284-287`).
- **Removal ambiguities:** `bleeding_corroded_blade` is in the category but has
  no dispeller branch, so it is not removed. Armor Crush bleed clears status
  and base damage but not duration or any named record. `unstable_compound` is
  not a pure removal: dispelling it triggers randomized immediate self damage
  using `sharp_blade_continuous_damage`, not `unstable_compound_damage`
  (`game/status_dispell.py:279-283`). That may also trigger Berserker-only
  receipt behavior if state is corrupted. These outcomes must not be described
  as a guaranteed clean cure without owner resolution.

### Warrior Berserker

#### Moon Slash

- **Target:** ranged-instant multi-target action with nominal quantity 2;
  command cardinality is `min(2, living legal enemies)`
  (`heroes/warrior.py:865`, `battle_api/adapter.py:2053-2066`).
- **Raw direct damage, per target:** one shared integer variation `v` in
  `[-3, 3]` is rolled for the action; each target receives
  `max(ceil((actor.damage + v - target.defense) * 2/3), 1)`
  (`heroes/warrior.py:914-925`). Ranged instant has no formation multiplier.
- **Bleed:** after a hit, a target that currently has Armor Breaker receives or
  refreshes Bleeding Moon Slash for duration 2, with the named record source
  replaced by the latest Berserker. Its future tick base is rerolled 6-10
  (`heroes/warrior.py:929-968`). Future damage is not part of preview. The
  status ticks once when duration moves 2 to 1, then is removed when it reaches
  zero (`game/status_effect_manager.py:1028-1050`).
- **Immediate Blood Frenzy drain:** if the actor already has Blood Frenzy, each
  processed target immediately heals the actor for
  `int(raw_pre-receipt_damage * 0.3)`, passed through normal healing modifiers
  (`heroes/warrior.py:925-928`). It is based on raw skill damage rather than HP
  actually removed after absorption/linked receipt.
- **Cooldown/control:** no cooldown or control.

#### Warlust

- **Target:** targetless self action (`heroes/warrior.py:866`).
- **Immediate self state:** removes the subset of active control-category
  statuses that the dispeller really supports, sets Warlust, enables control
  immunity, sets duration 2, and increases damage by
  `round(original_damage / 3)` (`heroes/warrior.py:972-994`). Cooldown is 3.
  Expiry subtracts that stored amount, clears Warlust, and disables control
  immunity (`game/status_effect_manager.py:1003-1012`).
- **Control-removal reachability:** player command ownership is denied while
  Glacier, Stun, Paralysis, Fear, or living-source Scoff controls the actor
  (`heroes/hero.py:1394-1450`). Therefore a normal player cannot choose Warlust
  to cure those states. The action's category also names Glacier and Stun, but
  the dispeller has no branch for either; supported branches among the category
  are Shadow Word Insanity, Fear, Scoff, and Paralysis
  (`heroes/hero.py:143`; `game/status_dispell.py:46-49`, `96-106`, `226-233`,
  `271-273`). Self-preview should only list a removal that is both present and
  actually reachable/supported; normally the list is empty.
- **Blood Frenzy:** Warlust does not directly trigger or change Blood Frenzy.
  Blood Frenzy is a separate probabilistic reaction when a Berserker survives
  damage (`heroes/hero.py:662-675`, `heroes/warrior.py:869-903`) and must not be
  promised by Warlust preview.

#### Strike of Meteorite

- **Target:** one legal melee enemy (`heroes/warrior.py:867`).
- **Raw direct damage:** for each integer `v` in `[-3, 3]`,
  `max(actor.damage + v - target.defense, 0)`
  (`heroes/warrior.py:998-1002`). Apply melee formation and receipt afterward.
- **Armor Breaker:** an accepted hit always applies the same 15%-of-original
  defence stack rule up to 3, or refreshes duration 2 at the cap. The apparent
  random gate is `roll <= 100`, so its outcome is certain even though it
  consumes RNG in live execution (`heroes/warrior.py:1010-1033`). Preview must
  not consume that roll.
- **Casting interruption:** active magic casting is always interrupted on an
  accepted hit (`heroes/warrior.py:1003-1008`). The skill is not marked control,
  so control immunity does not prevent this.
- **Immediate Blood Frenzy drain:** if already active, the actor heals for
  `int(raw_pre-formation, pre-receipt damage * 0.3)` through normal healing
  modifiers before the target takes damage (`heroes/warrior.py:1035-1040`).
- **Cooldown:** none.

## Finite contract recommendation

Keep `contractVersion: "1.0"` and all current targeted response fields. Make
only additive/relaxed changes:

1. Relax `BattlePreviewRequest.targetIds` from minimum 1 to minimum 0
   (`battle_api/models.py:181-185`). Validation must require exactly zero for
   audited `target_qty=0` actions and retain published command cardinality for
   all other skills. Permit a one-target draft only for audited quantity-2
   skills: Arcane Missiles, Thunder Pot, and Moon Slash. The real command's
   target requirement remains unchanged.
2. Add nullable `selfPreview` to `BattlePreviewData`; do not put the actor into
   `requestedTargetIds`, `selectedTargetIds`, or `targets`. A finite self fact
   contains `recipientId`, current/max HP, optional healing primary, and typed
   consequences. Targetless preview therefore has `targetIds=[]`, `targets=[]`,
   and a populated `selfPreview`, with no fake battlefield target.
3. Extend the discriminated consequence union only with finite Warrior facts:
   `armorBreaker`, `stun`, `castingInterrupted`, `scoff`,
   `healingReduction`, `wound`, `bleeding`, `resistanceBoost`,
   `controlImmunity`, `damageIncrease`, `statusRemoval`, `cooldown`, and (only
   when currently active and immediately applicable) `secondaryHealing`.
   Every non-target fact carries `recipientId`. Stack consequences carry
   `resultingStacks` plus `firstApplication|nextStack|durationRefresh`.
   Do not serialize arbitrary engine status dictionaries.
4. Add deterministic control prevention to the primary evaluator only when
   `skill.is_control_skill` and a live control-immunity status matches. This is
   required for Thunder Pot and must not be generalized from skill names.
5. Add small pure Warrior primitives that enumerate each skill's finite
   integer variation and state branch. The adapter then applies the existing
   formation and audited receipt helpers once. Self healing enumerates all
   discrete 18-20 values before rounding. No primitive calls RNG, mutates
   status, invokes `Skill.execute`, or clones a battle.

## Required invariants and validation matrix

- Preview remains under `session.lock`, verifies revision/actor/directive,
  uses `_legal_actions`/`_valid_target_ids`, and never installs session/global
  RNG (`battle_api/adapter.py:674-766`).
- Snapshot, HP, stats, status maps, named buff/debuff pools, durations, stacks,
  skill cooldowns, command cache, event sequence, output/status buffers, turn
  order, revision, session RNG state, and process-global RNG state must be
  byte/deep equal before and after success and every rejection.
- Same-seed action after preview must match an untouched same-seed control,
  including Strike of Meteorite's otherwise redundant RNG roll and every
  multi-target variation.
- Validate stale revision, wrong actor, unavailable/cooldown/passive/out-of-
  scope skill, dead/wrong-side/screened-rear/duplicate target, zero/extra
  targeted IDs, nonzero self IDs, quantity-2 draft/full behavior, Warlust
  control prevention, absorption, Void Connection, and prior Mage/Rogue/
  Priest/Paladin response compatibility.

## Decisions required before implementation

1. **Thunder Pot partial control immunity:** preserve and preview the current
   double self-boost/duplicate-record behavior, or authorize a separate live
   mechanics bug fix. Preview must not silently choose a corrected result.
2. **Antivenom and Unstable Compound:** decide whether potion-triggered
   explosion is intended. Until then, do not label it as an ordinary cure or
   invent a precise no-RNG result.
3. **Antivenom incomplete removals:** confirm whether Bleeding Corroded Blade
   and Armor Crush record/duration cleanup should be repaired separately. The
   current preview can safely claim only the mutations the live dispeller
   actually performs.
4. **Fatal Strike metadata:** effective live reduction is 70%, while its Debuff
   record says 0.8. Player-facing preview should use 70%; owner may separately
   reconcile the unused record.
5. **Control labels:** confirm that Shield Bash and Strike of Meteorite are
   intentionally allowed through Warlust. Marking them control skills would be
   a gameplay change and is outside this task.

