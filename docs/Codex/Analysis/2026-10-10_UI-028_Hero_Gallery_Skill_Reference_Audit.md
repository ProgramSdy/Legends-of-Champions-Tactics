# UI-028 — Hero Gallery Skill Reference Audit and Pilot Decision

**Date:** 2026-10-10  
**Status:** Implementation-approved pilot and bounded full-roster rollout plan  
**Scope:** Read-only Hero Gallery reference facts. This analysis does not alter
combat rules, construction, session state, progression, or Battle Information
Transparency.

## 1. Boundary map

`GET /api/v1/heroes` is the correct authority boundary. Its route in
`battle_api/app.py` delegates to `BattleAdapter.roster()` in
`battle_api/adapter.py`. The existing method reads configured property and
resistance workbook values plus `HERO_ROSTER`/`HERO_SKILL_INVENTORY`; it does
not construct a hero, create a battle, execute a skill, access progression, or
consume RNG. The response remains within the frozen `1.0` envelope.

The existing Gallery has two client boundaries:

- `fetchHeroRoster` accepts the lightweight existing roster used by Team
  Builder/Arena; it must remain compatible with existing mocks and consumers.
- `fetchHeroGalleryRoster` already demands the Gallery-only range, inventory,
  and unlock fields. It is the correct place to require the new additive
  reference metadata.

The Gallery currently imports editorial prose from
`web-ui/lib/manual/heroManualContent.ts`. Editorial text will move to authored
YAML, compiled and strictly validated into a generated TypeScript module before
the browser bundle is built. Browser fetches and request-time filesystem reads
are not an authority path.

## 2. Proposed typed catalogue shape

Every existing `skills[]` inventory item remains intact and receives a required
additive `reference` object. Stable `skillId` remains the join key; the browser
does not reconstruct a definition or parse Python source.

```text
reference = {
  target: { kind, maximumTargets? },
  skillType,
  attackType: classified | unclassified | notApplicable,
  damageNature: classified | unclassified | notApplicable,
  damageType: classified | unclassified | notApplicable,
  baseDamage: available | unavailable | notApplicable,
  baseHealing: available | unavailable | notApplicable,
}
```

`classified` carries a finite authoritative value. `unclassified` means a
damage concept applies but the engine definition does not supply its
classification; it is not a default. `notApplicable` means the concept does
not apply at all, such as damage nature for a pure heal or passive. Numeric
`available` has integer `minimum`, `maximum`, and explanatory basis/note;
`unavailable` has a stable reason and explanation; `notApplicable` has no
number. Validators forbid numeric fields in non-available variants.

Player-facing target kinds are adapter-owned semantics:

- `self` — target quantity zero/self action;
- `oneAlly`, `oneEnemy`, or `allyOrEnemy` — one legal selected target;
- `multipleAllies` or `multipleEnemies` — include the static maximum target
  count; and
- `teamAura` — non-command passive team effect.

They are derived from the audited adapter target-policy mapping (skill type,
target quantity, active/passive semantics, and current command policy), never
from raw `target_type="single"` alone. Battle legality remains dynamic and is
not published by this static catalogue.

## 3. Pilot formula audit

| Skill | Authoritative target semantics | Baseline result | Proof and limits |
| --- | --- | --- | --- |
| Priest Comprehensiveness — Holy Smite | One Enemy | Base Damage **16–22** | `19 + randint(-3, 3)` clamped at zero. It has no caster/target-stat input before receipt. The reference is pre-evasion, target resistance, formation, immunity, and HP receipt. |
| Priest Comprehensiveness — Shadow Word Pain | One Enemy | Base Damage **Unavailable** | Immediate value is `round((caster damage + randint(0,5) - target shadow resistance)/2)`. Target resistance is inseparable and generated-resistance compensation makes a simple workbook corner range unproved. The later DoT has separate lifecycle/fallback RNG and never has a total reference value. |
| Priest Comprehensiveness — Binding Heal | One Ally | Base Healing **22–28** | Selected recipient receives `25 + randint(-3,3)`. A different ally also causes a separate caster-only `20 + randint(-3,3)` (17–23) heal; it is not added to the target number. Attack/damage classifications are not applicable. |
| Paladin Protection — Hammer of Revenge | One Enemy | Base Damage **51–64** | Pre-Defence power is configured caster Damage 55–65 plus `randint(-4,-1)`. Target Defence/receipt are excluded. Current self-debuff bonus is separate: none +0; one +3–5; two +6–8; three-or-more +9–11. Its supplied attack type is Ranged Instant; damage nature/type are genuinely unclassified rather than inferred. |

The live Priest pure helpers can be used directly. If Hammer helpers are
extracted, they must only lift the existing arithmetic/constants and preserve
the live random-call count/order, pre-bonus clamp, and bonus ordering. No hero
is constructed at catalogue read time.

## 4. Full roster reference-audit ledger

All 31 approved inventory entries must publish target/skill/classification
states. The table records numeric-reference handling so unsupported values are
visible as unavailable rather than estimated. “Audit needed” means an entry is
intentionally unavailable until an exact formula proof is added; it is not a
claim that no live effect exists.

| Hero | Skill | Target semantic | Numeric-reference disposition |
| --- | --- | --- | --- |
| Priest C | Holy Smite | One Enemy | Available 16–22 (pilot) |
| Priest C | Shadow Word Pain | One Enemy | Unavailable — target-dependent immediate formula and separate periodic lifecycle |
| Priest C | Binding Heal | One Ally | Available target healing 22–28; separate caster-secondary condition |
| Priest D | Penance | Ally or Enemy | Unavailable pending branch/receipt audit; hybrid must retain separate damage/healing facts |
| Priest D | Holy Word Redemption | One Ally | Not applicable — status-only action |
| Priest D | Holy Word Punishment | Multiple Enemies (2) | Unavailable — immediate/periodic and target-count handling must be audited |
| Paladin R | Hammer of Anger | One Enemy | Unavailable — current Wrath conditional and receipt interactions |
| Paladin R | Crusader Strike | One Enemy | Unavailable — direct baseline/independent Wrath effect audit needed |
| Paladin R | Flash of Light | One Ally | Unavailable — current Wrath healing conditional |
| Paladin P | Hammer of Revenge | One Enemy | Available 51–64 plus separate verified debuff bands (pilot) |
| Paladin P | Shield of Righteous | One Enemy | Unavailable — damage plus stack/defence effect audit needed |
| Paladin P | Heroric Charge | One Enemy | Unavailable — direct/control/independent-effect audit needed |
| Paladin P | Holy Aura | Team Aura | Not applicable — passive round-start healing is status-owned, not a static per-action reference |
| Paladin H | Purify Healing | One Ally | Unavailable — healing plus eligible-status removal boundary |
| Paladin H | Holy Blast | Multiple Enemies (2) | Unavailable — ordered target/evasion behavior |
| Paladin H | Shield of Protection | Self | Not applicable — protection/status action |
| Mage C | Fireball | One Enemy | Unavailable — target receipt/resistance audit required |
| Mage C | Arcane Missiles | Multiple Enemies (2) | Unavailable — per-target multi target audit required |
| Mage C | Frost Bolt | One Enemy | Unavailable — immediate damage/Cold condition audit required |
| Warrior D | Devastate | One Enemy | Unavailable — defence/formation formula audit required |
| Warrior D | Shield Bash | One Enemy | Unavailable — damage/control effect audit required |
| Warrior D | Thunder Pot | Multiple Enemies (2) | Unavailable — multi-target/independent self effect audit required |
| Warrior WM | Fatal Strike | One Enemy | Unavailable — damage/debuff condition audit required |
| Warrior WM | Armor Crush | One Enemy | Unavailable — damage/stacked status conditions audit required |
| Warrior WM | Antivenom Potion | Self | Unavailable — self recovery/poison-resistance status audit required |
| Warrior B | Moon Slash | Multiple Enemies (2) | Unavailable — ordered multi-target/conditional audit required |
| Warrior B | Warlust | Self | Not applicable — self buff action |
| Warrior B | Strike of Meteorite | One Enemy | Unavailable — direct formula audit required |
| Rogue C | Sharp Blade | One Enemy | Unavailable — direct/bleed lifecycle audit required |
| Rogue C | Poisoned Dagger | One Enemy | Unavailable — direct/poison stack lifecycle audit required |
| Rogue C | Shadow Evasion | Self | Not applicable — self buff action |

This is deliberately conservative: UI-028 does not rebalance a skill or
replace an unavailable reference with a sampled, target-received, or
Transparency-specific value.

## 5. Editorial YAML plan

One YAML file per approved hero will have an exact stable `definitionId`,
multiline `introduction`, multiline `battleStyle`, and a sequence of
`skills: [{ skillId, introduction, tips? }]`. A sequence is necessary to
detect duplicate IDs. No mechanical/range/numeric/cooldown/status keys are
allowed. Validation will reject malformed YAML, unknown/stale IDs, duplicate
hero/skill IDs, missing coverage, empty required text, unsupported root/skill/
tip fields, wrong schema version, and mechanical numeric authority.

The generated registry preserves existing prose exactly. It is checked against
the static ten-hero/31-skill manifest. The README will explain the edit
directory, stable-ID requirement, content validation, and the required
dev/build restart or regeneration step.

## 6. Pilot and rollout gates

1. Add the additive Pydantic/roster contract plus pure audited reference
   registry; prove read-only/no-construction/no-RNG behavior and exact pilot
   results.
2. Add the validated YAML compilation boundary and Gallery facts presentation;
   retain the native accordion, tabs, ownership, assets, audio, and route.
3. Pass pilot API/range/content/UI tests, existing combat/Transparency tests,
   and responsive/keyboard checks.
4. Roll out the same explicit schema to all roster entries. The ledger's
   unavailable/not-applicable states remain truthful outcomes, not a deferred
   hidden fallback.

## 7. Risks and decisions

- The frozen v1 route remains compatible because existing fields persist and
  lightweight consumers do not require the new nested block.
- No client formula, source parsing, hero construction, skill callback,
  session, random sample, or browser-owned semantics is permitted.
- A Gallery reference is baseline explanatory information, never a live
  prediction or a Battle Information Transparency response.
- This audit found no owner decision required. Unavailable is the approved
  truthful state for an unproved numeric value.
