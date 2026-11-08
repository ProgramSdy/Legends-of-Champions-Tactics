# Current Task

**Status:** Completed

**Task:** UI-058 — Replace Battle Instruction Interface Image and Realign Markers

**Owner request date:** 2026-11-07

## Objective and background

In Battle Instruction → **04 Battle Interface**, replace the current clipped reference screenshot with the owner's newly attached full battle screenshot. Keep the entire new image visible, then verify and adjust every numbered clickable bubble so it identifies the correct control/region in that image. UI-057 has been formally marked Completed in its previous `Current_Task.md` and in `Completed.md`; no active task is being overwritten.

## Verified source and current implementation

- Owner image: `/var/folders/_2/tclj326x4x3ff1vpk4scvnm80000gn/T/codex-clipboard-2f637072-a1de-4a95-b026-cec125bd0da8.png` (PNG, **1913×954**). Core should copy this exact owner-supplied image into the existing public manual-image location early in the task so the temporary attachment path is not a runtime dependency. Do not modify the image content or fabricate a substitute.
- Current public image: `web-ui/public/game-images/manual/Battle_Instruction_Interface.png` (1597×822). `web-ui/components/manual/BattleInstructionExperience.tsx` displays that path and overlays nine marker buttons from `web-ui/content/battle-instruction/manual.yaml`.
- Current `web-ui/app/globals.css` forces `.instruction-battle-reference > img` into a **16:9** box with `object-fit: cover`, which crops these wider screenshots. The `.instruction-marker.marker-1` through `.marker-9` rules use percentages relative to that box; several positions therefore need rechecking after the image changes.

## Requirements

1. Replace the public Battle Interface reference with the exact supplied screenshot. Present the **whole image** at its natural aspect ratio (or within a proportional, fully visible image box), without cropping, stretching, or hidden edges. Retain a useful fallback if image loading fails.
2. Keep the nine existing marker topics, buttons, detail panel, active state, and pointer/touch/keyboard operation. Reposition each bubble against the actual new image: Team Information, Round & Turn Order, Battlefield Targets, Acting Hero, Skill Cards, Preview & Confirmation, Battle Log, Speed & Auto Battle, and Resign. Do not leave any marker pointing to an empty or unrelated area. Where one topic spans two areas, choose the clearest visible anchor and ensure its explanatory text remains truthful to this screenshot.
3. Anchor marker coordinates to the **rendered image content**, not a letterboxed or separately cropped container, so alignment remains stable as the page scales. Keep bubbles visible and clickable near image edges at desktop, tablet, and narrow widths without obscuring important labels. Preserve existing accessible names, selected-marker detail, and focus styling.
4. Do not change Battle gameplay, the live Battle UI, other Instruction chapters, Manual entry/exit or Back to Manual behaviour, or the owner image itself beyond copying it to the project. Preserve unrelated dirty/user changes.

## Acceptance and validation

- The full 1913×954 screenshot is visible in chapter 04 without clipping. At desktop and tablet widths, each of the nine markers is visually checked against the correct new-image region; at narrow width, the full image remains visible and markers still work (even if the image requires proportionate scaling).
- Clicking/focusing each marker selects the matching detail; no bubble covers another control or sits outside the image. The fallback and chapter navigation remain usable.
- Run the focused Battle Instruction UI check(s) and a brief rendered visual pass at desktop/tablet/narrow widths. Record the nine-marker alignment result, image dimensions, exact files changed, and any compromise for small screens in `Completed.md`; then mark this task complete. Avoid broad unrelated suites or repeated checks without a concrete failure. Do not commit or push without separate explicit owner approval.

## Agent assignment

**Complexity/risk:** Low-to-moderate UI/asset placement; marker accuracy is visual. Recommend only `ui-developer` for image replacement, proportional layout, all nine marker positions, and focused verification. Core can coordinate/close out directly; omit separate `project-manager`, `game-engine-developer`, `test-automator`, and `reviewer` because there is no distinct engine, contract, or independent-review workstream. Record actual dispatch and send the Documentation Planner one concise completion report or a genuine owner-decision blocker.

## Core pre-code gate — 2026-11-07

- **Sequence:** Inspect the nine existing topics/anchors and owner screenshot; copy the exact PNG into the existing public path; remove the image crop; re-anchor all nine buttons in image-relative coordinates; run focused tests and inspect desktop/tablet/narrow rendering before closeout.
- **Ownership:** Core is handling the scoped UI work directly. No sub-agent is dispatched: the owner did not request delegation, and this single asset/CSS/test workstream does not need parallel ownership. PM, engine, separate tester, and reviewer have no distinct workstream.
- **Risks:** A 1913×954 image scales small on narrow screens, making fixed-size markers occupy more of the artwork; the footer has several controls in a short band. Keep each marker centred on its anchor, reduce only the narrow marker size if necessary, preserve accessible list navigation, and disclose any remaining cramped presentation.

## Completion — 2026-11-07

Core copied the exact owner PNG into the existing public path (matching SHA-256), removed the displayed 16:9 crop, and realigned all nine marker centres to the new image. The overlaid guide caption no longer obscures the screenshot's bottom controls. Preview/confirmation copy now describes the bottom command button's changing state, and the generated read-only content was rebuilt. The focused Battle Instruction suite passed 6/6, including all nine marker selections and failed-image fallback; generated-content check and `git diff --check` passed. Isolated browser checks at 1597, 820, 390, and 320 CSS-pixel widths found the full 1913×954 image proportionally rendered, no horizontal overflow, and no marker outside or overlapping the image/another marker. All nine markers were clicked successfully at 320px. At 320px, the full screenshot necessarily scales too small to read its embedded labels, so the corresponding accessible marker detail/list remains the readable navigation. No commit or push.
