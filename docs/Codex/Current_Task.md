# Current Task

**Status:** Ready for Core

**Task:** UI-053 — Complete Profession Icons in Battle and Hero Gallery Intro

**Owner request date:** 2026-11-06

## Objective and background

Integrate the owner's four new profession icons for Mage, Rogue, and both Priest specializations into the existing Battle hero-card badge. Also show the corresponding profession icon for **all ten approved heroes** in the Hero Gallery's Hero Intro/profile heading, placed cleanly alongside the faculty and specialization identity. The owner's screenshots identify the four files and the intended Gallery region. UI-052, which registered six Warrior/Paladin icons in Battle, is marked Completed in its previous `Current_Task.md` and in `Completed.md`; no active task is being overwritten. Preserve UI-052's existing work and any other dirty/user files.

## Verified assets and mapping

The four new files exist as 128×128 PNGs in `web-ui/public/game-images/professions/icons/`:

| Hero definition ID | Exact new filename |
| --- | --- |
| `hero.mage.comprehensiveness` | `mage_comprehensiveness_profession_v01.png` |
| `hero.rogue.comprehensiveness` | `rogue_comprehensiveness_profession_v01.png` |
| `hero.priest.comprehensiveness` | `priest_comprehensiveness_profession_v01_128x128.png` |
| `hero.priest.discipline` | `priest_discipline_profession_v01.png` |

The six existing Warrior/Paladin mapping paths from UI-052 remain unchanged in `web-ui/lib/battle/assets.ts`. `web-ui/components/battle/HeroCard.tsx` already requests `kind: "profession"` by `hero.definitionId`, and the shared resolver supplies a fallback. `web-ui/components/manual/HeroGalleryExperience.tsx` currently renders the hero's figure and profile intro with faculty/specialization headings but no profession icon. Both standalone and battle-embedded Galleries use this component.

## Requirements

1. Add the four exact new paths to the existing stable-definition-ID profession registry. Battle Team Information cards on **both** sides must show the matching icon in their current gold-bordered top-right badge. Keep its 26px size, placement, card hierarchy, HP/status row, highlights, and Hero Stats control unchanged. Repeated heroes use the same definition icon. Preserve safe fallback for unknown/summoned definitions and failed artwork.
2. Reuse that same profession registry in the Hero Gallery profile **intro** for each of the ten approved heroes: four new icons plus the six existing Warrior/Paladin icons. Place a restrained gold-framed icon beside the faculty/specialization heading so it reads as part of hero identity, not as a skill or property. Keep the existing portrait/figure, title typography, intro copy, Battle Style, Properties, skill tabs, selection, and ownership logic. Do not put the icon in skill cards or change Gallery navigation.
3. Size and align the Gallery icon for desktop, tablet, and narrow screens without crowding long specialization names such as Comprehensiveness or causing overflow. Use the existing asset component/resolver and an accessible label that identifies the hero specialization; do not duplicate file mappings in React or show a broken-image marker.
4. Presentation only: do not edit owner PNGs, hero/skill/status data, API contracts, battle mechanics, Manual entry/exit, or unrelated routes.

## Relevant files and validation

- Likely edits: `web-ui/lib/battle/assets.ts`, `web-ui/components/manual/HeroGalleryExperience.tsx`, and tightly scoped Gallery CSS in `web-ui/app/globals.css`. `web-ui/components/battle/HeroCard.tsx` should need no change unless a concrete integration defect appears.
- Relevant guidance: `docs/web-ui/{WEB_UI_ARCHITECTURE,Style_Guide}.md`, the UI-052 completion record, and `docs/Codex/{Project_Rules,Agent_Roles}.md`.
- Focused checks: exact mapping for all ten IDs; four new Battle badges on friendly/enemy cards; all ten Gallery intro icons; unchanged six prior Battle icons; failed/missing-art fallback; responsive long names; and standalone plus battle-embedded Gallery rendering. Use one focused component/integration test and brief desktop/compact visual checks. Check the Gallery icon's crop, visual balance, and absence of horizontal overflow. Run relevant frontend typecheck and targeted lint only as warranted, plus `git diff --check`; avoid unrelated broad suites.
- Record exact files, checks, observed visual result, and limitations in `Completed.md`, then mark this task complete. Update `docs/web-ui/Style_Guide.md` if the new Gallery identity placement is a stable rule. Preserve unrelated dirty/user files. Do not commit or push without a separate explicit owner request.

## Agent assignments

**Complexity/risk:** Low, shared frontend asset mapping plus one Gallery identity placement. Recommend `ui-developer` for implementation and focused validation, or Core may own this small UI task directly if separate dispatch adds no value; record actual selection/dispatch truthfully. Omit `project-manager` (no coordination workstream), `game-engine-developer` (no engine/API change), separate `test-automator` (focused check can stay with UI owner), and `reviewer` (Core's targeted visual/interaction check is proportionate). Core should report once to the Documentation Planner at completion or for a genuine owner-decision blocker.
