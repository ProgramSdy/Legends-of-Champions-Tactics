# Current Task

**Status:** Completed

**Task:** UI-045 — Paladin Protection Skill and Passive Artwork Integration

**Owner request date:** 2026-11-02

**Completed:** 2026-11-02. All four supplied skill/passive images and the three approved status mappings are registered. The shared Battle, Gallery, and StatusIcon consumers render them without new command state; Scoff remains generic. Focused test, scoped lint, typecheck, diff check, and limited live desktop/compact checks passed. See `Completed.md`; no commit or push.

## Pre-code gate and ownership

Core confirmed the four 128×128 PNGs, three engine active skills plus non-commandable Holy Aura, the shared-status IDs, and the existing registry-driven consumers before editing. Core owned the small frontend registry/test change and live verification directly; no sub-agent was dispatched. PM, engine, separate test automator, and reviewer were omitted because there is no cross-system, contract, or independent-review workstream. The `ui-developer` recommendation was handled as Core's UI ownership rather than a separate dispatch. Existing dirty task/review records and owner images were preserved.

## Objective

Integrate the owner's four Paladin Protection images through the established battle skill-card, Hero Gallery, and applicable battle-status presentation flow, keeping the three selectable skills separate from the Holy Aura passive. UI-044 was marked Completed in the prior `Current_Task.md` and recorded in `Completed.md` before this replacement; no active task is being overwritten. The separate owner-requested Retribution Wrath Battle UI follow-up has also been implemented in the existing battle presentation without changing Python.

## Verified Assets and Exact Mapping

All four files exist as 128×128 PNGs under `web-ui/public/game-images/heroes/Paladin-Protection/skills/`:

| Purpose | Stable ID | Image filename |
| --- | --- | --- |
| Active skill: Hammer of Revenge | `skill.paladin.hammer_of_revenge` | `Paladin_Protection_Hammer_of_Revenge_128x128.png` |
| Active skill: Shield of Righteous | `skill.paladin.shield_of_righteous` | `Paladin_Protection_Shield_of_Righteous_128x128.png` |
| Active skill: Heroic Charge | `skill.paladin.heroric_charge` | `Paladin_Protection_Heroic_Charge_128x128.png` |
| Passive: Holy Aura | `skill.paladin.holy_aura` | `Paladin_Protection_Holy_Aura_128x128.png` |
| Conditional Hammer of Revenge debuff | `status.hammer_of_revenge` | Reuse Hammer of Revenge skill image |
| Shield of Righteous buff | `status.shield_of_righteous` | Reuse Shield of Righteous skill image |
| Holy Aura recipient buff | `status.holy_aura` | Reuse Holy Aura passive image |

The engine's `Paladin_Protection` has three active skills plus a non-commandable Holy Aura passive. Hammer of Revenge applies its debuff only under the existing Shield of Righteous condition; this task changes its icon, not that condition. Heroic Charge can apply `status.scoff`, but Scoff is a **shared status** also produced by Warrior and Death Knight skills. Do **not** globally replace Scoff's status icon with Heroic Charge art; that would misrepresent other sources. Keep the generic Scoff icon unless a later owner-approved source-specific art rule is provided. The authoritative skill ID retains the existing `heroric_charge` spelling despite the displayed “Heroic Charge” name.

## Requirements

1. Register the four exact paths by stable skill ID in `skillPresentation` (`web-ui/lib/battle/assets.ts`), with glyph/tone fallback. The three active Battle skill cards must display their images without altering commandability, targeting, cooldown, or card state. The Holy Aura battle card must display its image as an explicitly **non-selectable passive** (not a fourth command), using the existing passive-card behavior.
2. Hero Gallery's Active tab shows the three active images; Passive shows Holy Aura art. Keep the existing skill names, intro YAML, facts, accordion, and responsive layout.
3. Map only the three listed status IDs to their corresponding already-registered skill/passive art paths via `statusRegistry`. Shared `StatusIcon.tsx` should show them in Team Information and Hero Stats Active Effects, retaining helpful/harmful border, status name/tooltip, stack count, duration, focus, and image-failure glyph fallback. Leave `status.scoff` generic as explained above.
4. Presentation only. Do not change Python or any engine/passive mechanics, aura timing, status lifecycle, combat animation, API/contracts, catalogue metadata, or owner images.

## Relevant Files and Validation

- `web-ui/lib/battle/assets.ts` — expected primary registry change.
- `web-ui/components/battle/{BattleScreen,SkillCard,StatusIcon,HeroCard,HeroStatsDialog}.tsx` and `web-ui/components/manual/HeroGalleryExperience.tsx` — inspect consumers; edit only for a concrete presentation defect.
- `docs/ChatGPT/Image_Creation_Rule.md`, `docs/web-ui/{WEB_UI_ARCHITECTURE,Style_Guide}.md` — standing whole-set integration and small-size rules.

Verify exact asset paths; three active plus one passive art in battle and Gallery; the three appropriate status icons; non-commandability of Holy Aura; and fallback. One focused integrated UI check and a brief desktop/compact visual check are sufficient; record any statuses not manually induced instead of implying they were. No broad unrelated suites or separate review. Record actual evidence in `Completed.md`. Preserve unrelated dirty/owner-controlled files. Do not commit or push without a separate explicit owner request.

## Agent Assignments

Recommend only `ui-developer` for the registry mapping and focused presentation check, with Core owning the shared-Scoff audit, brief integration/visual verification, and closeout. Omit `project-manager` (no coordination workstream), `game-engine-developer` (no engine/API change), separate `test-automator` (focused check can stay with UI owner), and `reviewer` (Core's targeted check is proportionate). Core must record actual selection/dispatch before implementation and send the Documentation Planner one concise completion report or genuine owner-decision blocker.
