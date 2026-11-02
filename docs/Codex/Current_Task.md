# Current Task

**Status:** Completed

**Task:** UI-044 — Paladin Retribution Skill and Passive Artwork Integration

**Owner request date:** 2026-11-02

**Completed:** 2026-11-02. The three Retribution active skill images and separate passive Wrath image are registered; `status.wrath_of_crusader` reuses the passive path. Focused integrated test, scoped lint/diff check, and live Gallery/battle/status checks passed. See `Completed.md`; no commit or push.

## Pre-code gate and ownership

Core confirmed the four exact 128×128 PNGs exist and inspected the engine's three selectable Retribution skills plus Crusader Strike's `wrath_of_crusader` buff. The Gallery already has a separate passive `skill.paladin.wrath_of_crusader` entry. Select `ui-developer` for the shared registry mapping and one focused integrated UI check; Core owns the passive-versus-command audit, live visual check, and closeout. Omit PM, engine, separate test automator, and reviewer because this is a narrow presentation-only registration. Preserve unrelated dirty/owner files; do not commit or push.

## Objective

Integrate the owner's four Paladin Retribution images through the established whole-set presentation flow, preserving the distinction between three active skills and the Wrath of Crusader passive/buff. UI-043 was marked Completed in the prior `Current_Task.md` and recorded in `Completed.md` before this replacement; no active task is being overwritten.

## Verified Assets and Exact Mapping

All four files exist as 128×128 PNGs under `web-ui/public/game-images/heroes/Paladin-Retribution/skills/`:

| Purpose | Stable ID | Image filename |
| --- | --- | --- |
| Active skill: Hammer of Anger | `skill.paladin.hammer_of_anger` | `Paladin_Hammer_of_Anger_128x128.png` |
| Active skill: Crusader Strike | `skill.paladin.crusader_strike` | `Paladin_Crusader_Strike_128x128_Final.png` |
| Active skill: Flash of Light | `skill.paladin.flash_of_light` | `Paladin_Flash_of_Light_128x128.png` |
| Passive Gallery/skill presentation: Wrath of Crusader | `skill.paladin.wrath_of_crusader` | `Paladin_Wrath_of_Crusader_Black_BG_128x128.png` |
| Active buff: Wrath of Crusader | `status.wrath_of_crusader` | Reuse the Wrath of Crusader passive image |

The engine's `Paladin_Retribution` has three selectable skills. Crusader Strike activates/refreshes the `wrath_of_crusader` buff; Wrath of Crusader is presented as a passive, not a fourth selectable action. Hammer of Anger and Flash of Light do not create their own persistent status. Do not use Crusader Strike art for the Wrath buff or register the passive as a selectable command.

## Requirements

1. Register all four exact paths by stable skill ID in `skillPresentation` (`web-ui/lib/battle/assets.ts`) with appropriate glyph/tone fallbacks. The three active battle SkillCards show their own art; any existing passive SkillCard presentation may show Wrath art but must remain non-commandable. Preserve selected/disabled states and all command behavior.
2. The Hero Gallery's Active tab shows the three active images beside their names. Its Passive tab shows the Wrath of Crusader image beside that entry's name. Preserve accordion behavior, introduction YAML, facts, and narrow-width layout.
3. Map only `status.wrath_of_crusader` to the passive Wrath artwork, reusing its registered skill asset path. Show the buff art in Team Information and Hero Stats Active Effects through shared `StatusIcon.tsx`, preserving helpful styling, stack numeral, duration, tooltip/accessibility, and failed-image glyph fallback. Do not invent statuses for Hammer of Anger or Flash of Light.
4. Presentation only: no engine/passive activation, status stacking/lifecycle, healing effect, battle animation, API, catalogue metadata, or editorial changes. Do not modify the four owner-supplied images.

## Relevant Files and Validation

- `web-ui/lib/battle/assets.ts` — expected primary registry change.
- `web-ui/components/battle/{SkillCard,StatusIcon,HeroCard,HeroStatsDialog}.tsx` and `web-ui/components/manual/HeroGalleryExperience.tsx` — inspect shared consumers; edit only for a concrete defect.
- `docs/ChatGPT/Image_Creation_Rule.md`, `docs/web-ui/{WEB_UI_ARCHITECTURE,Style_Guide}.md` — existing whole-set image rule.

Check four exact asset paths, active/passive mapping, battle and Gallery appearances, and the Wrath status mapping/fallback. Use one focused integrated UI check and a brief visual check, including passive Gallery and at least one Wrath buff in Team Information/Hero Stats where practical; record what was not manually induced. Avoid broad unrelated suites or separate review. Record actual validation and completion in `Completed.md`. Preserve unrelated dirty/owner-controlled files. Do not commit or push without a separate explicit owner request.

## Agent Assignments

Recommend `ui-developer` only for registry mapping and focused UI validation; Core owns the passive-versus-command audit, brief visual verification, and closeout. Omit `project-manager` (no coordination workstream), `game-engine-developer` (no engine/API change), separate `test-automator` (focused UI check can stay with UI owner), and `reviewer` (Core's targeted check is proportionate). Core must record actual selection/dispatch before implementation and send the Documentation Planner one concise completion report or genuine owner-decision blocker.
