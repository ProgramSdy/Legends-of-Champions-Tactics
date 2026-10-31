# Current Task

**Status:** Completed

**Task:** UI-036 — Remove Redundant Manual Frame in Battle-Embedded Pages

**Owner request date:** 2026-10-31. The owner-provided screenshot shows the Hero Gallery inside a second, oversized “LEGENDS OF CHAMPIONS TACTICS / Game Manual” header and gold outer frame when opened from the battle's top-right Manual icon. The owner confirms the same flaw for Battle Instruction, but not for Stage Map-origin navigation. UI-035 is marked Completed in the prior `Current_Task.md` and `Completed.md`, so no active task is being overwritten.

## Objective

When the battle-origin Manual opens its Hero Gallery or Battle Instruction content, remove the redundant outer Game Manual header/frame and let the selected content be the visual focus. Keep the active battle mounted and recoverable, as fixed in UI-035.

## Requirements

1. Apply the change only to the **battle-embedded Gallery and Instruction views**. The initial Game Manual options dialog may retain its current header/frame. Stage Map-origin Manual and standalone Gallery/Instruction pages retain their existing presentation and navigation.
2. Neither embedded content view should display the large outer “LEGENDS OF CHAMPIONS TACTICS / Game Manual” title/header or an extra competing gold frame. Avoid double titles, doubled borders, and wasted top space. Preserve the content's own heading, back control, reading layout, scrolling, and dark-fantasy styling.
3. Keep an obvious, accessible way to close the embedded view directly back to the **same live battle**, despite removal of the current header's ×. A small × integrated into the content view/overlay is acceptable; support Escape, focus containment, focus restoration to the battle Manual trigger, pointer/touch/keyboard, and responsive desktop/tablet layouts. “Back to Manual” must still return to the Manual options within the battle, and closing from there must also preserve the battle.
4. Do not route to Stage Map, unmount/recreate the battle provider, reset selected skill/targets, replay events, pause/advance battle solely because of the Manual UI, or change combat/API/save behavior. Gallery/Instruction content remains the same; this is a presentation/interaction refinement only.

## Relevant Files and Root Cause

- `web-ui/components/manual/ManualDialog.tsx` currently renders one `<section className="manual-dialog ...">` with the same header and close button for `menu`, `heroes`, and `instruction`; the expanded content is nested in `.manual-dialog-content`.
- `web-ui/app/globals.css` defines `.manual-dialog.manual-dialog-expanded`, `.manual-dialog>header`, and `.manual-dialog-content` frame/scroll styles.
- `web-ui/components/manual/HeroGalleryExperience.tsx` and `BattleInstructionExperience.tsx` expose `embedded` content and `onBackToManual`; `web-ui/components/battle/BattleScreen.tsx` opens `ManualDialog` with `navigationMode="embedded"`. Stage Map uses its default route mode.
- Focused regression area: `web-ui/tests/ui-027-manual-gallery.test.tsx`, plus any focused battle/manual test that covers the UI-035 mounted-session guarantee. Read `docs/Codex/Project_Rules.md`, `Agent_Roles.md`, relevant web-ui architecture/style/flow docs, and these implementation paths before editing.

## Acceptance and Validation

- From an active battle, Manual → Hero Gallery and Manual → Battle Instruction each show only the intended content presentation, without the outer Game Manual title/header/frame. Check the supplied screenshot's desktop size and a compact supported viewport.
- Back to Manual and direct ×/Escape from either content view return to the proper destination with the **same mounted battle/session and current selection/playback state**. The initial Manual menu still works. Stage Map → Gallery/Instruction → Back retains its existing route and appearance.
- Run a focused interaction test for both embedded views, close/back/focus paths, and one short visual browser check; use proportional typecheck/lint only if needed. Do not rerun unrelated suites. Update `docs/web-ui/Style_Guide.md` or `Screen_Flow.md` only if the final UI convention changes; record completion in `docs/Codex/Completed.md`.

## Agent Selection Guidance

**Core pre-code selection (2026-10-31):** Small frontend-only layout/focus refinement. Dispatch `ui-developer` to own the embedded Manual subview frame/close control and focused UI interaction tests. Core owns screenshot/browser comparison, integration review, documentation, and closeout. Omit separate `project-manager` (no cross-workstream dependency), `game-engine-developer` (no engine/API change), `test-automator` (the UI owner can update one focused test), and `reviewer` (Core will perform a brief independent visual/interaction check of the low-risk presentation change). Preserve all dirty and owner files; no commit/push.

**Assessment:** Small frontend-only presentation/focus task. Recommend `ui-developer` alone for implementation and focused validation, with a brief Core lead review of the screenshot, close control, and battle-state continuity. No separate project-manager, game-engine-developer, or test-automator is needed; an independent reviewer is optional only if the chosen interaction introduces a new risk. Core must record actual selected/omitted roles and reasons before edits; do not claim participation by undispatched roles.

Preserve unrelated dirty files and the owner-controlled `UI_Review_Human.md`. Do not commit or push without a new explicit owner instruction. Send the Documentation Planner one concise completion report or a genuine owner-decision blocker.

## Completion (2026-10-31)

`ui-developer` implemented the embedded-only shell removal, close control, and
focused battle tests. Core reviewed the result in an isolated live Debug battle
at desktop and 800×600: both embedded views had their own heading without the
outer Manual header/frame, Back and direct ×/Escape preserved the exact mounted
battle shell, and focus returned to the Manual gear. At 800×600 there was no
horizontal overflow and vertical scrolling remained available. Stage Map
Manual kept its framed menu and standalone Instruction navigation. The browser
check also caught and removed a redundant content-level “GAME MANUAL” label in
embedded Instruction only; the standalone page retains it. Focused Manual and
Battle tests passed 42/42; battle-screen alone 27/27; typecheck passed; lint
reported 0 errors and 2 existing warnings; diff check passed before closeout.
No backend/API/save behavior or owner-controlled review file was edited by
UI-036. The owner subsequently explicitly requested commit and push, superseding
the earlier no-commit instruction for this turn.

**Owner follow-up:** The owner subsequently requested removal of the embedded
× from both Hero Gallery and Battle Instruction. Back to Manual and Escape
remain available; the initial Manual menu keeps its ×. This supersedes the
direct embedded × requirement above. No commit or push occurred because the
permission reviewer rejected staging the dirty worktree despite the request.
