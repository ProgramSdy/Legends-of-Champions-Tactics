# Codex Backlog

This file contains approved or proposed future work that is not currently active.

## Backlog Rules

- The project owner controls task priority.
- Codex should not start a backlog task merely because `Current_Task.md` is empty unless explicitly authorised.
- Each task should have a unique ID, clear outcome, priority, and acceptance criteria.

## Task Template

### TASK-0000 — Task title

**Priority:** Low / Medium / High
**Status:** Proposed / Approved / Blocked

**Objective:**
Describe the desired outcome.

**Acceptance Criteria:**

- Criterion 1

**Dependencies or Notes:**

- Note 1

## Tasks

### UI-015 — Preserve Team Builder Vertical Flow at Reduced Viewport Heights

**Priority:** High
**Status:** Completed — recorded in `docs/Codex/Completed.md`

**Objective:**
Repair the Team Builder layout so reducing browser viewport height preserves
normal vertical document flow. Team sections and the Hero Selection Matrix must
not overlap; when their combined content exceeds the viewport, the page must
scroll vertically.

**Scope and constraints:**

- Frontend presentation, layout, accessibility, and automated browser/UI
  validation only. Do not change gameplay logic, battle-create payloads, the
  Python adapter/API, or backend code.
- Preserve the current maximised desktop appearance and responsive
  **width** behaviour.
- Keep the existing Team Builder hero-card dimensions; do not solve the issue
  by excessively shrinking cards or scaling the full page by viewport height.
- Preserve all Team Builder interactions: battle size, slot assignment,
  filtering/paging, specified and Python-random enemy modes, seed handling,
  stage context, Back navigation, validation, and Enter Battle.
- Do not modify the owner-controlled
  `docs/web-ui/screenshots_debug/UI_Review_Human.md` or owner review assets.

**Investigation requirements:**

- Inspect `web-ui/components/battle/TeamBuilder.tsx`, its route/parent layout,
  and Team-Builder-specific CSS for fixed or viewport-relative heights,
  `height: 100vh`/`100dvh`, `max-height`, `calc(...vh...)`, `overflow: hidden`,
  absolute positioning, constrained grid rows, and flex/grid sizing that
  prevents natural content growth.
- Establish one normal-flow vertical stacking order: header/stage preview,
  Battle Rules, Your Team and Enemy Team, Hero Selection Matrix, then Enter
  Battle.
- Retain only appropriate scrolling. The Team Builder must gain normal vertical
  page scrolling when needed, without introducing a second unrelated scroll
  area or viewport-height compression.

**Acceptance criteria:**

- At full desktop height, the page remains essentially unchanged.
- At approximately 900 px, 700 px, 550 px, and 450 px viewport heights while
  retaining a wide desktop width, no card, text, border, or section overlaps.
- Your Team and Enemy Team cards retain their intended visual dimensions and
  remain fully contained in their sections.
- The Hero Selection Matrix always remains below the two team sections; Enter
  Battle remains reachable by vertical scrolling.
- A vertical scrollbar appears naturally once content exceeds the viewport.
- Current responsive width behaviour remains intact.
- Validate 1v1, 2v2, and 3v3 Team Builder layouts, including keyboard access
  and the existing live Enter Battle flow.

**Recommended agent assignment:**

- `project-manager` — inspect the height-layout boundary, maintain task scope,
  and record completion.
- `ui-developer` — own focused Team Builder/route CSS and component layout
  changes.
- `test-automator` — add or update deterministic viewport-height regression
  coverage and run browser checks across the required formats/heights.
- `reviewer` — independently verify normal document flow, protected Team
  Builder behaviour, accessibility, and the absence of API/gameplay changes.
- `game-engine-developer` is not expected unless investigation demonstrates a
  genuine backend or API defect; this task is otherwise frontend-only.

**Relevant files:**

- `web-ui/components/battle/TeamBuilder.tsx`
- `web-ui/app/globals.css`
- `web-ui/app/game/page.tsx`
- `web-ui/components/battle/BattleExperience.tsx`
- Existing Team Builder and route tests under `web-ui/tests/`
- `docs/web-ui/Screen_Flow.md`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/Codex/Completed.md`

**Validation evidence required:**

- Focused automated Team Builder tests that assert normal flow/no overlap or
  the layout constraints that guarantee it, plus relevant existing regression
  suites.
- Browser verification at all four required heights for 1v1, 2v2, and 3v3,
  including scrollbar/document-scroll evidence and an Enter Battle reachability
  check.
- `npm run typecheck`, lint, production build, task-scoped `git diff --check`,
  and `git status --short`.
- Record any pre-existing unrelated test failures separately; do not alter them
  merely to claim a fully green suite.

**Dependencies or notes:**

- The currently active UI-014 record must be completed and reset through the
  normal workflow before this prepared task replaces
  `docs/Codex/Current_Task.md`.
