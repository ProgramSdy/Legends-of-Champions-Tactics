# Current Task

**Status:** Ready for Core

**Task:** UI-061 — Add 1v1 Diagram to Battle Instruction Formations

**Owner request date:** 2026-11-08

## Objective and background

Battle Instruction → **03 Formation & Attack Types** now shows accurate 2v2 and 3v3 diagrams with the approved blue/red hero-slot shapes. Add the missing **1v1** duel diagram so the chapter covers every battle size. UI-060 is completed in `docs/Codex/Completed.md`; no active task is being replaced.

## Verified implementation

- `web-ui/components/manual/BattleInstructionExperience.tsx` renders Chapter 03's diagrams from `FORMATIONS` through `FormationDiagram`; currently only 2v2 and 3v3 entries exist. The current diagram component uses `web-ui/lib/battle/formations.ts` positions and the Chapter 02 blue/red silhouette.
- `web-ui/lib/battle/formations.ts` has `formationRegistry.duel`: one friendly visual slot to the left and one enemy visual slot to the right. `battle_api/adapter.py` `_formation_positions` assigns the sole 1v1 hero the gameplay position `front` and does not accept a formation choice for 1v1. Chapter 02 already describes 1v1 as “Duel — no formation choice” and “Front”.
- Styles are in `web-ui/app/globals.css`; focused manual tests are in `web-ui/tests/ui-050-battle-instruction.test.tsx`.

## Requirements

1. Add a **1v1 · Duel** diagram before the 2v2 diagrams in Chapter 03, with one blue friendly Hero 1 on the left, `VS` in the centre, and one red enemy Hero 1 on the right. Reuse the same rounded-top blue/red shape and visual language as the existing formation diagrams.
2. Show each sole hero as **Front** for gameplay clarity, and state or indicate **no formation choice**. Do not present a selectable formation or imply a Rear slot exists. Use the existing duel visual coordinates or equivalent symmetrical manual placement; ensure the accessible description is truthful.
3. Keep the new diagram proportionate and readable on desktop and narrow screens. Do not change the existing 2v2/3v3 diagrams, Chapter 02, battle formation rules, attack-type explanations, or Manual entry/exit. Preserve unrelated owner/dirty files.

## Acceptance and validation

- Chapter 03 has one accurate 1v1 diagram followed by the existing two 2v2 and three 3v3 diagrams. Blue/red colours, Hero 1 labels, Front classification, `VS`, and no-choice wording are clear.
- Focused Battle Instruction assertions cover the new duel diagram and unchanged existing diagram count/order. Brief desktop/mobile visual checks confirm no clipping or overlap. Record changed files/results in `Completed.md` and mark complete. No broad unrelated suite or commit/push without separate explicit owner approval.

## Agent assignment

**Complexity/risk:** Small UI-only follow-up. `ui-developer` owns the diagram, scoped styling, focused check, and visual verification; Core handles closeout. No separate project-manager, engine developer, test automator, or reviewer workstream is needed. Record actual dispatch and report once to the Documentation Planner upon completion or a genuine blocker.
