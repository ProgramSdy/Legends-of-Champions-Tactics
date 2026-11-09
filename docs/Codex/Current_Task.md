# Current Task

**Status:** Completed

**Task:** UI-064 — Refresh Battle Interface Manual Screenshot and Bubbles

**Owner request date:** 2026-11-09

## Objective and background

In Battle Instruction → **04 Battle Interface**, replace the current reference capture with the owner's new image, update the clickable bubbles to explain the newly visible target-hover information and the clickable Hero Stats control, and make the existing speed bubble describe **Battle Speed only**. Also remove the gold `FIELD GUIDE · SIX CHAPTERS` line from the Battle Instruction page header. UI-063 is completed in `docs/Codex/Completed.md`; no active task is being replaced.

## Verified implementation and assets

- New owner screenshot: `/var/folders/_2/tclj326x4x3ff1vpk4scvnm80000gn/T/codex-clipboard-c1f1c1b1-a2cb-487c-8d0c-1e1527784c90.png` (1919×954). Copy this exact PNG to the existing public manual-image path early; the temporary attachment path must not be a runtime dependency. Current public image: `web-ui/public/game-images/manual/Battle_Instruction_Interface.png` (1913×954).
- Header reference: `/var/folders/_2/tclj326x4x3ff1vpk4scvnm80000gn/T/codex-clipboard-a0f00233-d052-4671-93df-55ef07b91a27.png`.
- `web-ui/components/manual/BattleInstructionExperience.tsx` owns the image, numbered marker buttons/list/detail, fallback schematic, and the `FIELD GUIDE · SIX CHAPTERS` header line. `web-ui/app/globals.css` owns the image scaling and marker coordinates. `web-ui/content/battle-instruction/manual.yaml` owns the nine current marker topics; `web-ui/scripts/build-battle-instruction-content.mjs` validates the exact count and generates `web-ui/lib/manual/battleInstructionContent.generated.ts`.
- `web-ui/components/battle/HeroCard.tsx` confirms the small gold bar-chart button in each occupied hero card is the **View Hero Stats** control. It opens the read-only Hero Stats dialog. The new hover information above Paladin Bors is the supported target preview, distinct from the bottom `Cast Skill` command button.

## Requirements

1. Replace the existing public Battle Interface screenshot with the exact new image. Show its full frame without crop/stretch, preserving the current responsive/fallback behaviour. Do not alter the owner image itself other than copying it into the project.
2. Add a new clickable bubble on the **target-hover information panel above Paladin Bors**. Its detail should explain that, for supported selected skills/targets, the preview can show decision information such as expected direct damage, hit chance, and target HP before confirmation; values are estimates, not guaranteed outcomes. Anchor the bubble to this panel, not to the Paladin figure or the bottom command button.
3. Add a distinct clickable bubble on a visible **gold bar-chart button inside a hero card** (the owner's “status button”). Explain clearly that this is a button: select/click/activate it to open Hero Stats and inspect current battle attributes and active effects. Do not imply clicking a status-effect icon has the same action, and do not change the live button's behaviour.
4. Keep the existing bottom command explanation but make it a separate **Command Confirmation** bubble tied to the `Cast Skill` control. Remove the old combined “Preview & Confirmation” ambiguity. Replace “Speed & Auto Battle” with **Battle Speed** only; explain the `×1`, `×1.5`, `×2` presentation-speed controls. Do **not** add or retain an Auto Battle bubble. This changes only the manual: do not remove or change the live Auto Battle control.
5. Keep the other existing topics (Team Information, Round & Turn Order, Battlefield Targets, Acting Hero, Skill Cards, Battle Log, Resign), so the final guide has **11** coherent, uniquely numbered bubbles/topics. Update the editable YAML, exact-count validation, generated content, accessible labels, marker list/detail, and fallback schematic as needed. Re-anchor **all** marker centres to the new image; avoid bubbles obscuring the hover panel, Hero Stats button, or each other. Ensure every marker and list item activates its matching detail on desktop and narrow screens.
6. Remove only the decorative gold `FIELD GUIDE · SIX CHAPTERS` line above the Battle Instruction title. Preserve `Back to Manual`, the title/subtitle, six chapters, navigation, and header spacing without a dead gap.

## Out of scope and acceptance

- No live Battle UI, preview calculation, Hero Stats behaviour, gameplay, save, API, Manual entry/exit, or other chapter redesign. Preserve unrelated dirty and owner-controlled files.
- The new full screenshot is visible; the hover-preview and Hero Stats buttons each have their own correctly placed, clickable bubble; command confirmation and Battle Speed have separate truthful explanations; no bubble describes Auto Battle. The gold header line is absent with the title layout intact.
- Run the focused Battle Instruction/content tests and generated-content check for **11** topics. Visually verify all 11 markers against the screenshot at desktop/tablet/narrow widths, including clicks and fallback; check marker bounds/overlap and header layout. Record changed files, result, and any narrow-screen compromise in `Completed.md`, then mark complete. Avoid broad unrelated suites or repeated review. Do not commit or push without separate explicit owner approval.

## Agent assignment

**Complexity/risk:** Low-to-moderate UI/asset/content placement with marker-accuracy risk. Assign only `ui-developer` to image replacement, bubble copy/coordinates, schema/count update, focused checks, and visual verification; Core owns final closeout. No separate PM, game-engine developer, test automator, or reviewer workstream is needed. Record actual dispatch and report once to the Documentation Planner at completion or for a genuine owner-decision blocker.

## Core pre-code gate — 2026-11-09

**Assessment:** One UI/content/asset workstream with moderate marker-coordinate and narrow-screen risk. No gameplay, API, or Manual navigation change. Existing UI-062/UI-063 and owner files are dirty and will be preserved. Sequence: inspect owner capture and current marker/content boundary → copy exact capture and replace nine-topic mapping with eleven → focused content/interaction checks → desktop/tablet/mobile marker inspection → Core documentation closeout.

**Selected and dispatched role:** `ui-developer` owns the public screenshot, Battle Instruction component, scoped CSS, Manual YAML/generated content/schema, focused tests, and browser visual checks. Core owns final diff review and completion documentation. PM, engine, separate test automator, and reviewer are omitted because this is one bounded presentation workstream with no changed authority or contract.

## Completion — 2026-11-09

The UI developer (`/root/ui064_ui`) copied the exact owner screenshot, produced eleven distinct, re-anchored Manual markers and matching content, updated the fallback/schema/tests, and removed only the decorative header kicker. Core verified the image checksum and reviewed the scope, then updated the Style Guide and completion record. Focused tests passed 17/17; generated-content check, frontend typecheck, targeted ESLint, and `git diff --check` passed. Browser inspection at 1613px, 820px, and 320px found no horizontal overflow, overlapping/out-of-bounds markers, or broken marker-list interactions. The scaled screenshot's embedded detail remains naturally tiny at 320px, so the numbered list and detail panel carry the readable explanation. No Python/API, owner-controlled review file, commit, or push change was made. See `docs/Codex/Completed.md` for the exact file list and evidence.
