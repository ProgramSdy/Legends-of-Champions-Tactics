# Completed Codex Tasks

Completed work should be appended in reverse chronological order, with the newest entry first.

## Completion Entry Template

### TASK-0000 — Task title

**Completed:** YYYY-MM-DD

**Summary:**

Brief description of the completed result.

**Files Changed:**

- `path/to/file`

**Validation:**

- Command or check — Result

**Unresolved Issues or Follow-up:**

- None, or list remaining items.

---

## 2026-08-02 — UI-009: Remove the Redundant Selected-Target Rectangle and Text

**Summary:**

Removed only the `.battle-figure.targeted::after` pseudo-element that drew the
redundant selected-target border and `TARGET` label. The retained
`.battle-figure.targeted` gold drop-shadow continues to distinguish selected
targets; legal target IDs, pointer and keyboard selection, crosshair feedback,
and command payloads are unchanged.

**Agent Selection and Contributions:**

- Complexity/risk assessment — low, isolated frontend CSS cleanup. The
  `project-manager`, `ui-developer`, and `test-automator` participated as
  assigned. `game-engine-developer` was not selected because no authoritative
  state, adapter, API, or game rule could change. `reviewer` was not selected
  because the deterministic focused regression and live checks cover the
  narrow selector removal.
- `project-manager` — constrained the scope, ran the integration/toolchain
  checks, completed browser evidence, and maintained the task workflow.
- `ui-developer` — removed only the legacy pseudo-element declaration while
  retaining the selected-target glow and interaction implementation.
- `test-automator` — added a regression that verifies selected state persists
  while the legacy CSS pseudo-label rule and text are absent; it also retained
  multi-target selection coverage.

**Files Changed:**

- `web-ui/app/globals.css`
- `web-ui/tests/battle-screen.test.tsx`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`

**Validation:**

- `cd web-ui && npx vitest run tests/battle-screen.test.tsx tests/stage-two-automation.test.tsx --reporter=dot` — 31 passed.
- `cd web-ui && npm run typecheck && npm run lint && npm run build` — passed;
  vinext emitted its existing informational route-classification note.
- Live browser validation at `http://localhost:3001/` with the API on 8001:
  in 1v1, selecting a legal target showed the retained `targeted` class and
  crosshair beforehand, no visible `TARGET` text, `::after` content `none`,
  and a successful Sharp Blade cast. In 3v3, Priest Discipline's multi-target
  skill selected two enemy figures, retained both targeted highlights without
  label text, and proceeded to the authoritative cast.
- `git diff --check` for UI-009 files — passed.
- Full frontend suite — 103 passed, 2 failed in existing UI-006/UI-007
  formation-history assertions (`trio` former-y comparison and stale duel
  scale expectation). Neither test or implementation area is changed by
  UI-009.

**Unresolved Issues or Follow-up:**

- Repair the two stale UI-006/UI-007 formation-history assertions in a
  separately authorised formation/test-maintenance task.

---

## 2026-08-02 — UI-008: Apply Priest Discipline Figure and Make Battle Entry Countdown and Opening Turns Playable

**Summary:**

Registered the supplied Priest Discipline battlefield figure and replaced the
standalone entry screen with a `3 → 2 → 1 → START` overlay on the fully
composed live battlefield. The adapter now additively returns an authoritative
pre-automatic-opening `openingSnapshot` and `playOpening` flag when an
automatic actor opens the battle. React starts from that snapshot, presents
the returned stable-ID events once in order, and reconciles to the final
authoritative snapshot/revision before enabling commands. Python continues to
select and resolve every engine action; the client does not simulate AI or
combat outcomes.

**Agent Selection and Contributions:**

- Complexity/risk assessment — high, cross-boundary lifecycle work. All five
  configured roles participated. The project manager completed the
  game-engine coordination wave directly because the active-agent capacity was
  occupied by the selected frontend, test, and review work.
- `project-manager` — sequenced ownership boundaries, implemented and verified
  the adapter lifecycle, integrated documentation and browser evidence, and
  protected owner-controlled review inputs and supplied artwork.
- `ui-developer` — registered the final figure, implemented the composed
  countdown, presentation-queue reconciliation/cancellation/input gating, and
  frontend opening tests.
- `game-engine-developer` — through the coordinated adapter wave, added the
  minimal compatible opening snapshot/script fields without changing seeded
  game choices, events, or final session state.
- `test-automator` — added deterministic adapter/API and Priest-orientation
  coverage; the project manager ran its Python suite in the project virtual
  environment.
- `reviewer` — independently re-reviewed contract authority, async queue
  cancellation/retry/deduplication, documentation, and tests; approved with no
  blocking findings.

**Files Changed:**

- `battle_api/adapter.py`
- `tests/test_battle_adapter.py`
- `tests/test_battle_api.py`
- `web-ui/lib/battle/assets.ts`
- `web-ui/lib/battle/types.ts`
- `web-ui/lib/battle/liveProvider.ts`
- `web-ui/lib/battle/usePresentationQueue.ts`
- `web-ui/components/battle/BattleExperience.tsx`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/app/globals.css`
- `web-ui/tests/ui-008-opening.test.tsx`
- `web-ui/tests/stage-two-automation.test.tsx`
- `web-ui/tests/battle-backgrounds.test.tsx`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`
- `docs/web-ui/PYTHON_ADAPTER_API.md`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/web-ui/Style_Guide.md`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`

**Validation:**

- `.venv/bin/python -m pytest -q tests/test_battle_adapter.py tests/test_battle_api.py` — 72 passed; one non-failing Starlette/TestClient deprecation warning.
- `cd web-ui && npm run typecheck && npm run lint` — passed.
- Focused frontend suites (`ui-008-opening`, opening automation, battle
  backgrounds, BattleScreen, and Team Builder) — 42 passed.
- `stage-two-ui` plus `ui-008-opening` after compatibility reconciliation —
  14 passed.
- Live local validation on `http://localhost:3001/` with the API at port 8001:
  Priest Discipline loaded from the exact direct URL on both sides; friendly
  transform was `none` and enemy transform was the expected horizontal matrix.
  At the enemy-first seed-1 1v1 opening, the `3` overlay showed full HP, an
  empty log, and disabled skills; afterwards the Python-authored Venombane
  opening action played once and commands enabled at Lioren's player boundary.
- Independent reviewer disposition — approved, no blocking findings.

**Unresolved Issues or Follow-up:**

- The full frontend suite has three pre-existing formation-history assertions
  that conflict with later owner-authorised formation/scale values; the
  UI-008-specific and provider compatibility suites pass. The unrelated
  owner-controlled `docs/web-ui/screenshots_debug/UI_Review_Human.md` has an
  existing trailing-whitespace finding, so it was not modified and is excluded
  from task-scoped whitespace checking.
- A future presentation test may add a fixture opening containing healing and
  buff/debuff effects; current opening tests cover movement, damage, ordering,
  cancellation, retry, and deduplication, while backend coverage verifies
  status metadata.

---

## 2026-08-02 — UI-Entry-001: Add Pre-Battle Countdown

**Summary:**

Added a centered `3 → 2 → 1 → START` countdown when the Team Builder enters a
battle. The live battle screen is deliberately not mounted until the countdown
finishes, so the initial Python-backed session creation request and all battle
interaction begin after `START`. The countdown uses the fixed BG03 backdrop
and does not change engine authority, battle rules, or the API contract.

**Agent Selection and Contributions:**

- This was a focused frontend lifecycle and presentation change. `project-manager`
  and `ui-developer` participated. `game-engine-developer` was not selected
  because the delayed mount prevents a session request without altering Python
  behavior. `test-automator` and `reviewer` were not selected because durable
  lifecycle coverage and live browser validation directly cover the isolated
  client behavior.
- `project-manager` — selected a delayed mount rather than a cosmetic overlay,
  preserving the requirement that the battle session has not started yet.
- `ui-developer` — implemented the countdown state machine, centered visual,
  delayed mount boundary, and regression coverage.

**Files Changed:**

- `web-ui/components/battle/BattleExperience.tsx`
- `web-ui/app/globals.css`
- `web-ui/tests/battle-backgrounds.test.tsx`
- `web-ui/tests/ui-002-team-builder.test.tsx`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/Codex/Completed.md`

**Validation:**

- Countdown/background and Team Builder suites — 8 passed across 2 files.
- Frontend TypeScript typecheck — passed.
- Regression coverage confirms the battle creation request is absent during
  countdown and occurs after `START`.
- Live 1440×720 browser check — centered `3` measured at x 651.6–788.4 within
  the 1440px viewport; after the sequence, the countdown was removed and the
  live battlefield mounted.

**Unresolved Issues and Follow-up:**

- None for the requested countdown behavior.

---

## 2026-08-02 — UI-Target-001: Show Crosshair During Hero Target Selection

**Summary:**

Added explicit crosshair feedback to valid battlefield hero targets while a
selected skill still needs targets. It works for friendly and enemy targets.
For a single-target skill, the cursor returns to normal after the one target is
selected. For a multi-target skill, it stays crosshair until the required
maximum target count is selected, then returns to normal. Invalid/disabled
heroes keep the normal cursor throughout.

**Agent Selection and Contributions:**

- This was a focused frontend interaction-state correction. `project-manager`
  and `ui-developer` participated. `game-engine-developer` was not selected
  because Python continues to author legal target IDs and target counts.
  `test-automator` and `reviewer` were not selected because the targeted
  interaction regression and live browser verification directly cover this
  isolated UI-state behavior.
- `project-manager` — verified the authoritative legal-action boundary was
  preserved and constrained the change to presentation state.
- `ui-developer` — applied the cursor to the actual target button, tied it to
  remaining target count, and excluded invalid targets.

**Files Changed:**

- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/app/globals.css`
- `web-ui/tests/battle-screen.test.tsx`
- `docs/web-ui/Style_Guide.md`
- `docs/Codex/Completed.md`

**Validation:**

- Focused battle-screen suite — 16 passed, including friendly/enemy and
  multi-target cursor-state coverage.
- Frontend TypeScript typecheck — passed.
- Live 1v1 browser verification — the valid target control computed to
  `crosshair` after skill selection and to `default` after selecting its target.

**Unresolved Issues and Follow-up:**

- None for target-selection cursor feedback.

---

## 2026-08-02 — UI-007 Follow-up: Set 1v1 Hero Scale to 1.1

**Summary:**

Set the friendly and enemy 1v1 formation scale to 1.1 as requested. The
existing duel y-position remains 80% and the two sides remain symmetric. This
does not affect 2v2, 3v3, the 1.5× duel HP/status panel treatment, formation
coordinates for multi-hero formats, or any battle rules.

**Agent Selection and Contributions:**

- This was a low-risk formation-constant adjustment. `project-manager` and
  `ui-developer` participated. `game-engine-developer`, `test-automator`, and
  `reviewer` were not selected because the scope has no engine/API boundary and
  focused regression coverage directly validates the changed constants.
- `project-manager` — identified the current live value discrepancy and kept
  the requested change to the duel scale only.
- `ui-developer` — applied the symmetric 1.1 scale and added regression
  assertions for both duel sides.

**Files Changed:**

- `web-ui/lib/battle/formations.ts`
- `web-ui/tests/ui-007-regressions.test.tsx`
- `docs/web-ui/Style_Guide.md`
- `docs/Codex/Completed.md`

**Validation:**

- Focused UI-007 regression suite — 17 passed.
- Frontend TypeScript typecheck — passed.

**Unresolved Issues and Follow-up:**

- None for the requested 1v1 scale adjustment.

---

## 2026-08-02 — UI-HP-001: Enlarge 1v1 Health and Status Panel

**Summary:**

Enlarged the complete 1v1 battlefield overhead health/status box by 1.5×. The
duel-only scale is bottom-anchored, preserving the calculated clearance above
the hero. Shared 2v2 and 3v3 health/status boxes, hero artwork, formations,
and battle behavior are unchanged.

**Agent Selection and Contributions:**

- This was an isolated CSS presentation correction. `project-manager` and
  `ui-developer` participated. `game-engine-developer`, `test-automator`, and
  `reviewer` were not selected because no game/API behavior changed and the
  existing focused UI regression suite plus live layout measurement directly
  validates the small scoped change.
- `project-manager` — confirmed the requested scope and retained cross-format
  separation.
- `ui-developer` — added the duel-only, bottom-anchored scale rule and updated
  the durable geometry and style-guide documentation.

**Files Changed:**

- `web-ui/app/globals.css`
- `web-ui/tests/ui-007-regressions.test.tsx`
- `docs/web-ui/Style_Guide.md`
- `docs/Codex/Completed.md`

**Validation:**

- Focused UI-007 regression suite — 17 passed.
- Frontend TypeScript typecheck — passed.
- Live 1440×720 1v1 browser measurement — both health/status panels measured
  198px wide (1.5 × the shared 132px width), with 8px clearance above the
  hero figure.

**Unresolved Issues and Follow-up:**

- None for the requested 1v1 panel enlargement.

---

## 2026-08-02 — UI-BG-001: Use Only Battle Scene Background 03

**Summary:**

Retired BG01 and BG02 from live battle presentation. Every newly started
battle now uses the single fixed
`/game-images/battle-scenes/backgrounds/Battle_Scene_BG03.png` background;
no random selection is performed. The background remains cosmetic only and is
not connected to Python battle authority, the battle seed, or the API contract.

**Agent Selection and Contributions:**

- This was a low-risk frontend presentation-constant change. `project-manager`
  and `ui-developer` participated. `game-engine-developer` was not selected
  because no authoritative behavior or contract changed. `test-automator` and
  `reviewer` were not selected because the updated focused regression test and
  typecheck directly cover the isolated behavior.
- `project-manager` — scoped the retired assets, confirmed the absence of
  engine/API impact, and recorded validation evidence.
- `ui-developer` — replaced the random registry with the fixed BG03 constant,
  updated the battle consumers and regression test, and aligned the web UI
  architecture documentation.

**Files Changed:**

- `web-ui/lib/battle/battleBackgrounds.ts`
- `web-ui/components/battle/BattleExperience.tsx`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/tests/battle-backgrounds.test.tsx`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`

**Validation:**

- `npx vitest run tests/battle-backgrounds.test.tsx --reporter=dot` — 1 test
  passed.
- `npm run typecheck` — passed.
- Application-source search for `Battle_Scene_BG01`, `Battle_Scene_BG02`,
  `pickRandomBattleBackground`, `BATTLE_BACKGROUNDS`, and `Math.random` — no
  remaining matches.

**Unresolved Issues and Follow-up:**

- BG01 and BG02 asset files remain preserved in the repository; they are no
  longer referenced by the live application.

---

## 2026-08-02 — UI-007 Follow-up: Correct Formation Depth Scale Ordering

**Summary:**

Corrected the duo and trio formation scale ordering after their ground anchors
were moved for the enlarged figure treatment. In each team, the lower,
visually nearer position now renders larger than the farther position. The
change is symmetric for friendly and enemy teams; it does not alter 1v1,
shared hero-art geometry, HP/status positioning, assets, or battle rules.

**Agent Selection and Contributions:**

- This was a narrow presentation-registry correction. `project-manager` and
  `ui-developer` participated. `game-engine-developer`, `test-automator`, and
  `reviewer` were not selected because the change only exchanges established
  scale constants, has no engine/API contract effect, and is covered by the
  existing focused regression suite plus direct live geometry validation.
- `project-manager` — identified the mismatch between vertical depth and the
  retained scale order, kept the scope to the formation registry, and recorded
  validation evidence.
- `ui-developer` — reversed the duo/trio scale values symmetrically while
  preserving all coordinates and shared layout geometry.

**Files Changed:**

- `web-ui/lib/battle/formations.ts`
- `docs/web-ui/Style_Guide.md`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`

**Validation:**

- Focused UI-007 regression tests — 17 passed.
- Frontend TypeScript typecheck — passed.
- Live browser validation at 1440×720 against the running client:
  - In 2v2, the farther 82% row measured 161.68×266.96px and the nearer 100%
    row measured 175.44×289.68px on both sides.
  - In 3v3, the 75%, 88%, and 100% rows measured 137.6×227.2px,
    147.92×244.24px, and 154.8×255.6px respectively on both sides.
  - Every overhead HP/status panel retained approximately 8px of clearance
    above its figure.

**Unresolved Issues and Follow-up:**

- None for this correction. Future formation changes must preserve the rule
  that a nearer, lower slot uses a larger scale.

---

## 2026-08-02 — UI-007 Follow-up: Double Battlefield Hero Image Size

**Summary:**

Doubled the shared battlefield hero-art footprint from 86×142px to 172×284px.
The enlarged footprint applies identically to final direct artwork and fallback
figures in 1v1, 2v2, and 3v3. The figure control/anchor expands with the art,
while overhead HP/status panels remain independently positioned above it.
Original formation scales are preserved, so the rendered artwork is a true
100% increase in every format rather than a smaller visual increase caused by
scale reduction.

**Agent Selection and Contributions:**

- This was a direct, narrow presentation-only follow-up. `project-manager`,
  `ui-developer`, and `test-automator` participated. `game-engine-developer`
  and `reviewer` were not selected because no engine rules, adapter/API
  contract, assets, or cross-boundary behavior changed.
- `project-manager` — confirmed the literal rendered-size requirement,
  prevented formation-scale reduction from weakening it, and recorded the
  validation evidence.
- `ui-developer` — enlarged and re-anchored the artwork/control geometry,
  kept overhead UI unscaled, retained aura centering and direct-art-only enemy
  mirroring, and repositioned formation anchors for the enlarged art.
- `test-automator` — added and updated the 172×284 footprint and overhead
  clearance regression contract.

**Files Changed:**

- `web-ui/app/globals.css`
- `web-ui/lib/battle/formations.ts`
- `web-ui/tests/ui-007-regressions.test.tsx`
- `docs/web-ui/Style_Guide.md`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`

**Validation:**

- Focused UI-007 geometry tests — 17 passed.
- Full frontend Vitest suite — 103 passed across 10 files.
- TypeScript typecheck, ESLint, production build, and task-scoped
  `git diff --check` — passed. The existing Vinext route-classification warning
  remains non-failing.
- Live browser validation at 1440×720 against the running Python-backed client:
  - 1v1 artwork increased from 110.08×181.76px to 220.16×363.52px; opposing
    feet share the 483.24px baseline.
  - 2v2 artwork increased from 87.72×144.84px / 80.84×133.48px to
    175.44×289.68px / 161.68×266.96px.
  - 3v3 artwork increased from 77.4×127.8px / 73.96×122.12px /
    68.8×113.6px to 154.8×255.6px / 147.92×244.24px /
    137.6×227.2px.
  - Every aura had 0px horizontal center drift. Overhead HP/status panels
    remained visible with a 6.99–7px gap above the artwork; no overlap or
    clipping was observed.

**Unresolved Issues and Follow-up:**

- None for the requested size and layout correction. Future owner art review
  may refine aesthetic spacing, but the requested doubling and layout safety
  are verified.

---

## 2026-08-02 — UI-007: Correct Battlefield Figure Geometry, Target-Bound Effects, Builder Identity, and Page Scrolling

**Summary:**

Corrected cross-format battlefield presentation without changing combat rules.
Direct final artwork and fallbacks now share one bottom-aligned figure
footprint, with centered auras and 1v1 opposing feet on a common baseline.
Healing, buffs, and debuffs now render on the authoritative event target.
The adapter additively emits `statusPresentation` on `statusApplied` events so
React renders blue buffs, red debuffs, and neutral compatibility without
recreating game-status classification. Friendly and enemy lunges now move in
opposite, correct directions. Specified enemy selections use the same
`Faculty - Major` labels as player selections, and the Team Builder and Asset
Registry gained finite keyboard-scrollable desktop regions.

**Agent Selection and Contributions:**

- Complexity/risk assessment — high, medium-high cross-boundary user-visible
  bug-fix. All five configured roles participated because it spans frontend
  geometry, adapter event metadata, regression coverage, browser validation,
  and independent review.
- `project-manager` — sequenced the frontend and adapter streams, preserved
  Python authority and owner-controlled review inputs, consolidated validation,
  resolved reviewer follow-up tests, and updated completion documentation.
- `ui-developer` — implemented shared figure/aura geometry, target-bound
  effects, side-aware movement, Builder labels, and accessible scroll regions.
- `game-engine-developer` — added backwards-compatible authoritative
  `statusPresentation: "buff" | "debuff" | "neutral"` metadata to
  `statusApplied`, with contract tests and documentation; battle mutation,
  targeting, duration, ordering, and outcomes remain unchanged.
- `test-automator` — added deterministic UI-007 regressions across duel, duo,
  and trio; both target sides; typed buff/debuff effects; and actual friendly/
  enemy lunge events. It completed focused, full-suite, and toolchain checks.
- `reviewer` — independently verified target/source correctness, adapter
  compatibility, mirror/transform boundaries, scrolling accessibility, and
  documentation scope. Its initial closeout findings (browser evidence,
  broader side/format tests, and completion evidence) were addressed before
  this record.

**Files Changed:**

- `battle_api/adapter.py`
- `tests/test_battle_adapter.py`
- `tests/test_battle_api.py`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/components/battle/TeamBuilder.tsx`
- `web-ui/lib/battle/types.ts`
- `web-ui/lib/battle/fixture.ts`
- `web-ui/app/globals.css`
- `web-ui/app/assets/page.tsx`
- `web-ui/tests/ui-007-regressions.test.tsx`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`
- `docs/web-ui/PYTHON_ADAPTER_API.md`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/web-ui/Style_Guide.md`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`

**Validation:**

- Backend adapter tests — 53 passed.
- Backend API tests — 15 passed; one existing Starlette/TestClient deprecation
  warning.
- Full Python suite — 98 passed; the same non-failing warning only.
- Focused UI-007 frontend regression suite — 16 passed.
- Full frontend Vitest suite — 102 passed across 10 files.
- TypeScript typecheck, ESLint, and production `vinext` build — passed. The
  build retains its existing route-classification warning only.
- Task-scoped `git diff --check` — passed. A full-worktree check reports only
  pre-existing trailing whitespace in the owner-controlled
  `docs/web-ui/screenshots_debug/UI_Review_Human.md`; that file was not edited
  by this task and is excluded from the UI-007 patch.
- Browser validation at 1440×720 against live `http://localhost:3001` and
  `http://localhost:8001`: 1v1 direct/fallback figures each measured
  110.08×181.76px with shared feet at 375.74px, 0px aura drift, and a 15.36px
  HP/art gap. Duo and trio retained the same per-slot direct/fallback geometry.
  Live events showed friendly-right/enemy-left lunge classes, red enemy debuff
  and green friendly-healing target effects. Blue buffs were deterministically
  exercised from the typed authoritative cue because no convenient live engine
  action emitted one during the review session.
- Team Builder (720/883px) and Asset Registry (720/2801px) each exposed
  `overflow-y: auto`, a stable scrollbar gutter, focusability, and successful
  keyboard scrolling to their overflow range. Specified enemy options rendered
  all eight labels as `Faculty - Major`.
- No browser console, runtime, API, or network failure was observed during the
  validated live flows. An initial `make dev` launch found both expected ports
  already occupied; direct health and HTTP checks confirmed the existing
  adapter/frontend processes were healthy and used for validation.

**Reviewer Disposition:**

- Approved after the requested browser evidence, cross-format/both-side tests,
  and completion record were added. No remaining code-level correctness,
  security, or API-compatibility blocker was found.

**Unresolved Issues and Follow-up:**

- Final visual-art quality and OS-specific native scrollbar appearance still
  benefit from future owner review; CSS contracts and live geometry are
  validated.
- The owner-controlled human review file and supplied screenshots remain
  intentionally untouched and must be staged separately only by owner intent.

---

### DOC-002 — Establish Mandatory Five-Agent Cooperation

**Completed:** 2026-07-28

**Summary:**

Established the project owner's golden rule that every Legends of Champions
Tactics task must activate and use all five configured Codex agents. Added a
single detailed role and workflow reference, made it mandatory startup reading,
added explicit five-agent assignments to the current-task template, and
documented proportional no-change reviews and coordinated execution waves so
mandatory participation does not expand scope.

**Agent Contributions:**

- `project-manager` — selected the authoritative document locations, resolved
  the all-tasks interpretation, defined startup order, sequencing, and
  acceptance checks.
- `ui-developer` — reviewed frontend ownership, accessibility, Next.js, and
  frontend-integration responsibility wording; no application changes were
  required.
- `game-engine-developer` — reviewed engine, adapter, API, event, and contract
  ownership wording; no application changes were required.
- `test-automator` — verified agent names and configuration files, startup
  links, contradiction removal, Markdown integrity, diff scope, and
  owner-controlled file protection.
- `reviewer` — independently reviewed the final documentation, identified the
  escaped-Markdown blocker, and approved the corrected result with no remaining
  findings.

**Files Changed:**

- `docs/README.md`
- `docs/Codex/Project_Rules.md`
- `docs/Codex/Agent_Roles.md`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`

**Validation:**

- Confirmed all five exact `.codex/agents/*.toml` files exist and their internal
  names match the documented agent names.
- Confirmed all five roles appear in `Agent_Roles.md` and the current-task
  assignment template.
- Confirmed `README.md` and `Project_Rules.md` require reading
  `Agent_Roles.md` and all five configurations before every task.
- Searched for stale contradictory wording such as small-task or
  relevant-agents-only exceptions — no matches in the authority documents.
- Searched the four workflow authority/template documents for accidental
  escaped headings, lists, numbered markers, code spans, and underscores — no
  matches.
- Path-scoped `git diff --check` for the four workflow authority/template
  documents — passed.
- Independent reviewer re-review — approved with no blocking or non-blocking
  findings.
- Confirmed the owner-controlled
  `docs/web-ui/screenshots_debug/UI_Review_Human.md` was not edited.

**Unresolved Issues or Follow-up:**

- The configured `game-engine-developer.toml` and `ui-developer.toml`
  descriptions are narrower than their project-wide roles in
  `Agent_Roles.md`. The new document intentionally supplements them with the
  owner's project-specific responsibilities. A future owner-authorised
  configuration-alignment task may update those TOML definitions.
- Existing UI-001 application and documentation changes in the working tree
  predate DOC-002 and were preserved; they are not changes introduced by this
  documentation-rule task.

---

### UI-001 — Fix Battle Screen Log, Skill Layout, HP/Status Display, and Status Tooltips

**Completed:** 2026-07-28

**Summary:**

Implemented the five approved corrections in `UI-REVIEW-001`. The live battle
provider now preserves session-opening adapter events, and the presentation
queue renders ordered authoritative `BattleEvent.message` entries while
retaining all remaining log events when animation playback is skipped. The
bottom panel now gives the independently scrolling Battle Log more width and
keeps skill cards compact and height-independent. Battlefield figures show
current/max HP above the hero and active status icons below it. The status
presentation registry now covers every identifier emitted by the live adapter,
and battlefield tooltips are pointer- and keyboard-focus accessible.

**Files Changed:**

- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`
- `docs/web-ui/UI_Review.md`
- `web-ui/app/globals.css`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/components/battle/StatusIcon.tsx`
- `web-ui/lib/battle/assets.ts`
- `web-ui/lib/battle/liveProvider.ts`
- `web-ui/lib/battle/types.ts`
- `web-ui/lib/battle/usePresentationQueue.ts`
- `web-ui/tests/battle-screen.test.tsx`
- `web-ui/tests/components.test.tsx`
- `web-ui/tests/stage-two-automation.test.tsx`
- `web-ui/tests/stage-two-ui.test.tsx`

The owner-controlled
`docs/web-ui/screenshots_debug/UI_Review_Human.md` was read only and was not
modified.

**Validation:**

- `cd web-ui && npm test -- --run` — 42 tests passed across four files.
- `cd web-ui && npm run typecheck` — passed.
- `cd web-ui && npm run lint` — passed.
- `cd web-ui && npm run build` — passed for `/` and `/assets`.
- `.venv/bin/python -m pytest` — 29 tests passed; one non-failing Starlette
  `TestClient` deprecation warning.
- Live browser review at `http://localhost:3001/` with the adapter on port
  `8001` confirmed the initial engine events, ordered live command events, hero
  HP values, status placement, and resolved status tooltips.
- At a 1280×720 viewport, 13 live events produced a 175px scroll region inside
  the Battle Log's bounded 120px viewport; skill cards remained 94px high and
  the document remained fixed at the 720px viewport height.
- Pointer focus on the battlefield Arcane Guard icon displayed its real name,
  description, and remaining duration.
- Compared the completed screen against
  `docs/web-ui/screenshots_debug/battle_27_07_2026-01.png` and all five owner
  annotations.

**Unresolved Issues or Follow-up:**

- Status display metadata remains an explicit frontend registry and must be
  extended whenever the adapter begins emitting a new status ID. Truly
  unmapped IDs still use the intentional `Unknown status` diagnostic fallback.
- The adapter's generic status-applied event message currently exposes stable
  status and combatant IDs. This is authoritative event output, but a future
  owner-approved contract task could add display-ready status metadata without
  changing combat rules.
- Recommended next documentation task: define an approved status-definition
  metadata boundary in the web UI contract or document the registry-sync
  responsibility explicitly.

---

### DOC-001 — Repair Documentation Foundation

**Completed:** 2026-07-26

**Summary:**

Repaired escaped Markdown control syntax across the 15 newly scaffolded
documentation files without changing their intended meaning or filling
unconfirmed placeholders. Added retrospective baseline completion records for
Stage 1 and Stage 1.5/Stage 2. Updated the frozen v1 battle contract to describe
the implemented Stage 2 HTTP adapter and the current pre-submission
`legalActions` behaviour. Completed the task through the new Codex
task-management workflow.

**Files Changed:**

- `docs/README.md`
- `docs/Codex/Project_Rules.md`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Backlog.md`
- `docs/Codex/Completed.md`
- `docs/GDD/Game_Design_Document.md`
- `docs/GDD/Combat_System.md`
- `docs/GDD/Hero_System.md`
- `docs/GDD/Skill_System.md`
- `docs/Technical/Architecture.md`
- `docs/Technical/Networking.md`
- `docs/Technical/Save_System.md`
- `docs/web-ui/UI_Review.md`
- `docs/web-ui/Screen_Flow.md`
- `docs/web-ui/Style_Guide.md`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`

**Validation:**

- Searched all 15 scaffolded files for escaped headings, emphasis, inline-code
  markers, numbered-list punctuation, and list markers — no accidental matches.
- Inspected the documentation-only diff and reread every changed Markdown file.
- Compared the contract wording with `battle_api/adapter.py`,
  `battle_api/app.py`, `web-ui/lib/battle/liveProvider.ts`, and the current
  adapter/frontend tests.
- Confirmed DOC-001 introduced no application-code, test, configuration, or
  asset changes.

**Unresolved Issues or Follow-up:**

- The GDD, Technical, Screen Flow, Style Guide, and UI Review documents remain
  intentional placeholders pending confirmed content.
- Historical onboarding statements remain preserved as point-in-time analysis
  and should not be treated as current architecture.
- Recommended next documentation task: owner-authorized promotion of confirmed
  current architecture into `docs/Technical/Architecture.md` and
  `docs/Technical/Networking.md`, followed by documenting the implemented web
  screen flow.

---

## Retrospective baseline records

The following entries predate the Codex task-management system. They are
recorded retrospectively from Git history, repository files, existing
documentation, test evidence, and the corresponding completion reports.

### Stage 1 — Battle Web UI Vertical Slice

**Completed:** 2026-07-25 (confirmed by commit `8d8e47fd`)

**Summary:**

Added the Stage 1 presentation-only Next.js battle-screen vertical slice while
preserving Python as the gameplay authority. The work introduced a stateful
mock battle provider, versioned TypeScript battle types, semantic presentation
events, authoritative snapshot reconciliation, reusable battle components,
asset fallbacks, an asset-gallery route, desktop-responsive styling, and the
initial frozen v1 battle data contract. It also added the repository onboarding
analysis and Codex agent definitions used for later development.

**Files Changed:**

- `.codex/agents/*.toml`
- `docs/onboarding/*.md`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `web-ui/app/`
- `web-ui/components/battle/`
- `web-ui/lib/battle/`
- `web-ui/public/game-assets/classes/`
- `web-ui/tests/`

**Validation:**

- Git commit `8d8e47fd` records the completed Stage 1 implementation and its
  committed Vitest component/battle-screen suites.
- `web-ui/README.md` records the intended TypeScript, ESLint, production-build,
  and Vitest validation workflow.
- No preserved Stage 1 terminal transcript with exact pass counts was found in
  the repository, so no historical count is asserted here.

**Unresolved Issues or Follow-up:**

- Stage 1 used scripted fixture outcomes and did not yet connect the browser to
  the Python engine.
- Hero, skill, and effect artwork remained intentionally placeholder-ready.
- Live adapter integration, live error handling, and multi-team formation
  previews were deferred to Stage 1.5/Stage 2.

---

### Stage 1.5 / Stage 2 — Formations and Live Python Battle Integration

**Completed:** 2026-07-26 (confirmed by commit `d7f82487`)

**Summary:**

Extended the Next.js battle client with centralized 1v1, 2v2, and 3v3
formations and connected the live 1v1 Ragnar-versus-Nighthawk scenario to a
thin FastAPI adapter over the existing Python engine. The adapter invokes the
existing `Game` and `Skill.execute` rule path, exposes the frozen v1 contract,
returns ordered semantic events and authoritative snapshots, validates
revisioned commands, and provides idempotent command handling. Sessions retain
independent seeded or entropy-backed random state under engine/session locks.
The client gained an HTTP live provider, authoritative reconciliation,
structured loading/error/rejection states, live/mock development routes, asset
diagnostics, ended-battle rendering, and browser-reviewed presentation states.

**Files Changed:**

- `battle_api/`
- `requirements-api.txt`
- `pytest.ini`
- `tests/`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`
- `docs/web-ui/PYTHON_ADAPTER_API.md`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/web-ui/screenshots/`
- `web-ui/components/battle/`
- `web-ui/lib/battle/`
- `web-ui/tests/`
- `web-ui/README.md`

**Validation:**

- Git commit `d7f82487` records the dedicated Stage 1.5/Stage 2 implementation
  and completion state.
- Python test suite — 29 passed; one non-failing Starlette `TestClient`
  deprecation warning.
- Frontend Vitest suite — 39 passed across four test files.
- ESLint — passed.
- TypeScript type checking — passed.
- Production frontend build — passed for `/` and `/assets`.
- Real FastAPI HTTP smoke validation covered health, battle creation, a legal
  command, ordered events, HP reconciliation, and the next-turn transition.
- Browser review covered live skill selection, target selection, resolving and
  reconciled turns; disconnected/retry handling; the asset gallery; and mock
  2v2/3v3 formations. Desktop checks from 1366×768 through 1920×1080 found no
  figure overlap or document overflow.
- Independent review concluded with no unresolved P0/P1/P2 findings and a
  ship verdict.

**Unresolved Issues or Follow-up:**

- Sessions remain process-local, single-worker, non-persistent, unauthenticated,
  and non-expiring.
- A separately hosted frontend still requires an explicit API origin and CORS
  configuration or a same-origin proxy.
- Live 2v2/3v3, durable replay, broader status/hero mappings, production art,
  and coordinated dependency upgrades remain deferred.
- Mutation-delta event inference may require richer typed engine
  instrumentation as immunity, zero-damage actions, summons, and more heroes
  enter live scope.

---

## 2026-07-28 — QA-001: Five-Agent Quality Audit of UI-001

**Summary:**

Re-audited the completed UI-001 battle-screen work through all five configured
project roles. The audit repaired Battle Log auto-follow, separated
battlefield status interaction from target controls, hardened keyboard target
selection, suppressed accepted equal-revision event replay, made adapter status
event ordering deterministic, expanded all-current-status coverage, repaired
the UI review Markdown, and corrected the retrospective Stage 1.5/Stage 2
commit record. The independent reviewer found no blocking correctness or scope
issues.

**Agent Contributions:**

- `project-manager` — reconciled UI-001 acceptance criteria, audit scope,
  historical evidence, and required browser/owner-file checks.
- `ui-developer` — audited and corrected log auto-follow, status/target
  interaction structure, keyboard targeting, and focused UI regressions.
- `game-engine-developer` — audited adapter/provider boundaries, prevented
  equal-revision replay, and stabilized status-event ordering.
- `test-automator` — added exhaustive status metadata and cross-boundary
  registry tests and ran the integrated validation suite.
- `reviewer` — independently reviewed the final integrated diff, validation
  evidence, scope, and owner-file protection; reported no blocking findings.

**Files Changed:**

- `battle_api/adapter.py`
- `tests/test_battle_adapter.py`
- `web-ui/app/globals.css`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/components/battle/StatusIcon.tsx`
- `web-ui/lib/battle/assets.ts`
- `web-ui/lib/battle/liveProvider.ts`
- `web-ui/lib/battle/types.ts`
- `web-ui/lib/battle/usePresentationQueue.ts`
- `web-ui/tests/battle-screen.test.tsx`
- `web-ui/tests/components.test.tsx`
- `web-ui/tests/stage-two-automation.test.tsx`
- `web-ui/tests/stage-two-ui.test.tsx`
- `docs/web-ui/UI_Review.md`
- `docs/Codex/Completed.md`
- `docs/Codex/Current_Task.md`

**Validation:**

- Frontend Vitest suite — 51 passed across four test files.
- TypeScript type checking — passed.
- ESLint — passed.
- Production frontend build — passed for `/` and `/assets`; vinext emitted its
  informational route-classification note.
- Python adapter/API suite — 31 passed; one non-failing Starlette `TestClient`
  deprecation warning.
- Live browser review on frontend port 3001 and adapter port 8001 verified
  authoritative event rendering, Battle Log auto-follow, stable layout,
  mapped status focus content, pointer targeting, and Enter targeting.
- At 1280×720, 13 log entries remained inside a 120-pixel-high scrolling list
  (`scrollHeight` 175, `scrollTop` 55), skill cards remained 94 pixels high,
  and document dimensions matched the viewport.
- `git diff --check` — passed.
- Owner-controlled
  `docs/web-ui/screenshots_debug/UI_Review_Human.md` retained its baseline
  SHA-256:
  `91c816cdaad251ff794a8b06f630ca270ce9f3f886342f6e2bf5f4b3c220fdd3`.

**Unresolved Issues:**

- Frontend status descriptions remain a duplicated metadata registry. The new
  guard verifies complete identifier coverage but cannot prove that prose
  remains semantically synchronized with future engine changes.
- The explicit target-button keyboard workaround activates Space on keydown
  rather than native keyup timing. It prevents duplicate default activation
  and is non-blocking, but exact invocation-count coverage is recommended.
- The existing Starlette/httpx test-client deprecation warning remains.

**Recommended Follow-up:**

- Define an owner-approved single source or generated path for status
  presentation metadata, then add exact Enter/Space invocation-count coverage
  if the explicit browser keyboard workaround remains necessary.

---

## 2026-07-29 — UI-002: Team Builder and Live 2v2/3v3 Battles

**Summary:**

Added Team Builder as the normal web entry point, exposed the eight approved
hero definitions through the Python adapter, and extended live engine-backed
battles to configurable 1v1, 2v2, and 3v3. Player teams remain
player-controlled; enemies support random or specified composition and
computer or player control. The adapter drains existing Python AI turns,
preserves ordered authoritative events and snapshots, supports repeated hero
definitions through slot-qualified instance IDs, and handles the approved
roster's skill/target/status shapes. Finished battles now provide an accessible
return action that resets the complete frontend battle lifecycle.

**Agent Contributions:**

- `project-manager` — mapped cross-boundary dependencies, froze the additive
  creation contract, selected a permissive duplicate/overlap policy where no
  design restriction was authorised, and defined acceptance gates.
- `ui-developer` — implemented roster loading, Team Builder, typed creation,
  multi-target interaction, completion dialog, return/reset, status metadata,
  and frontend tests.
- `game-engine-developer` — implemented the eight-hero factory/roster API,
  multi-team session creation, validation, seeded random enemies, computer-turn
  draining, authoritative incapacitated-turn skipping and forced Scoff
  targeting, stable IDs, legacy target-shape compatibility, statuses, and
  backend/API tests.
- `test-automator` — added all-eight-hero live-action, player-controlled enemy,
  malformed-roster, and fresh-session lifecycle coverage and ran the integrated
  validation suite.
- `reviewer` — independently reviewed authority, API/RNG/AI behavior, legality,
  accessibility, reset, tests, browser evidence, scope, and documentation. No
  blocking implementation issue remained; modal focus and roster validation
  recommendations were implemented before completion.

**Files Changed:**

- `battle_api/adapter.py`
- `battle_api/app.py`
- `battle_api/models.py`
- `tests/test_battle_adapter.py`
- `tests/test_battle_api.py`
- `web-ui/app/globals.css`
- `web-ui/app/page.tsx`
- `web-ui/components/battle/BattleExperience.tsx`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/components/battle/TeamBuilder.tsx`
- `web-ui/lib/battle/assets.ts`
- `web-ui/lib/battle/liveProvider.ts`
- `web-ui/lib/battle/types.ts`
- `web-ui/tests/stage-two-ui.test.tsx`
- `web-ui/tests/ui-002-team-builder.test.tsx`
- `docs/web-ui/UI_Review.md`
- `docs/web-ui/UI_Review_002.md`
- `docs/web-ui/Screen_Flow.md`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`
- `docs/web-ui/PYTHON_ADAPTER_API.md`
- `docs/Codex/Completed.md`
- `docs/Codex/Current_Task.md`

**Validation:**

- Frontend Vitest suite — 57 passed across five test files.
- TypeScript type checking — passed.
- ESLint — passed.
- Production frontend build — passed; vinext emitted its informational
  route-classification note.
- Python suite — 59 passed; one existing non-failing Starlette/httpx
  test-client deprecation warning.
- Seeded adapter stress covered 30 live 1v1/2v2/3v3 configurations for up to
  six human-command cycles.
- Live browser review covered specified/player-controlled 1v1,
  random/computer-controlled 2v2, and specified/computer-controlled 3v3.
- Browser review confirmed enemy-player legal action and Enter targeting,
  Python AI turn draining, all selected combatants, battle completion after
  four human actions, result dialog, return/reset, and fresh relaunch.
- At 1280×720, live 3v3 rendered six figures without document overflow; the
  Battle Log remained 120 pixels high and internally scrolled, while skill
  cards remained 94 pixels high.
- Live Poisoned Dagger status metadata displayed correctly on pointer hover and
  keyboard focus.
- The owner-controlled file retained its task-start SHA-256:
  `1d4ce91e6f2a6200bbf4bc0a434560c91ea25910e37daa5f80e6743277247230`.

**Unresolved Issues:**

- Sessions remain process-local, unauthenticated, non-expiring, and
  single-worker.
- The legacy engine uses module-global randomness and stateful specialization
  behavior; the adapter retains locks and per-session RNG state, but the
  approved roster is not an exhaustive balance/interaction proof.
- Status presentation descriptions remain duplicated frontend metadata, with
  cross-boundary identifier coverage but no generated prose source.
- One existing Starlette/httpx test-client deprecation warning remains.

**Recommended Follow-up:**

- Define an owner-approved generated source for status presentation metadata
  and separately plan durable authenticated session storage before any
  production multiplayer or multi-worker deployment.

---

## 2026-07-30 — ASSET-001: Create Empty Game Image Asset Folder Structure

**Summary:**

Created the future game-image hierarchy under the Next.js public asset root at
`web-ui/public/game-images/`. The structure contains only zero-byte tracking
markers and has no runtime wiring, image content, metadata, manifests, samples,
or application changes.

**Agent Contributions:**

- `project-manager` — confirmed `web-ui/public` as the static root, inspected
  repository conventions, defined the exact tracking-marker policy, and
  coordinated scope.
- `ui-developer` — created the required hierarchy with one zero-byte
  `.gitkeep` in each leaf directory.
- `game-engine-developer` — confirmed the presentation-only hierarchy has no
  engine, adapter, API, or contract impact.
- `test-automator` — verified exact directories, markers, emptiness, naming,
  image absence, unchanged source/config/tests, and build rationale.
- `reviewer` — independently approved the structure-only result and confirmed
  the documented naming/count resolutions.

**Final Tree:**

```text
web-ui/public/game-images/
├── battle-scenes/
│   ├── backgrounds/.gitkeep
│   ├── foregrounds/.gitkeep
│   └── overlays/.gitkeep
├── heroes/
│   ├── portraits/.gitkeep
│   ├── figures/.gitkeep
│   ├── skills/.gitkeep
│   └── status-attach/.gitkeep
├── faculty/
│   └── icons/.gitkeep
├── ui/
│   ├── frames/.gitkeep
│   ├── panels/.gitkeep
│   ├── badges/.gitkeep
│   └── placeholders/.gitkeep
├── effects/
│   ├── combat/.gitkeep
│   ├── magic/.gitkeep
│   ├── particles/.gitkeep
│   └── shared/.gitkeep
└── others/.gitkeep
```

**Files Changed:**

- `web-ui/public/game-images/**/.gitkeep` — 17 zero-byte leaf markers.
- `docs/Codex/Completed.md`
- `docs/Codex/Current_Task.md`

**Validation:**

- Correct root confirmed as `web-ui/public/game-images/`.
- 23 unique directories exist: the root, six top-level categories, and 16
  additional children. `others` is both a top-level category and a leaf.
- 17 leaf directories and exactly 17 `.gitkeep` files.
- Every `.gitkeep` is zero bytes; no other files exist under the new root.
- No image files were created or added.
- All directory components use lowercase kebab-case.
- Existing `web-ui/public/game-assets/` content remained unchanged.
- No application source, route, style, test, configuration, or build-script
  file changed.
- Scoped `git diff --check` passed.
- No build was run because unreferenced zero-byte public markers cannot affect
  compilation or runtime behavior.
- Independent reviewer reported no blocking finding.

**Deviations and Conflicts:**

- The task diagram used `status_attach`, while requirement 7 and the acceptance
  criteria require lowercase kebab-case. `status-attach` was used and the
  underscore variant was not created.
- The tree has 23 unique directories, not 24. A count of 24 double-counts
  `others`, which is both a top-level directory and a leaf. No unauthorized
  directory was invented to reach that count.

**Unresolved Issues:**

- The current UI continues using the existing `/game-assets/` namespace.
  Populating or wiring `/game-images/` requires a separately authorized task.

**Recommended Follow-up:**

- Define asset naming, dimensions, formats, and registry/wiring rules only when
  the project owner assigns the future image-production task.

---

## 2026-07-30 — ASSET-002: Organize Hero Assets by Profession

**Summary:**

Replaced the four shared hero asset leaf folders with profession-specific
folders for all eight heroes approved by the current Web UI/API roster. Each
profession contains empty `portraits/`, `figures/`, `skills/`, and
`status-attach/` leaves tracked by zero-byte `.gitkeep` files. No images,
application code, configuration, contracts, or tests were changed.

**Agent Contributions:**

- `project-manager` — defined scope, sequenced the restructure, protected
  unrelated working-tree content, and maintained workflow documentation.
- `ui-developer` — confirmed that the owner-requested faculty-specialization
  hierarchy is the appropriate frontend-facing organization and applied the
  explicit title-case folder naming.
- `game-engine-developer` — verified all eight professions against
  `battle_api.adapter.HERO_ROSTER` and confirmed no engine, adapter, API, or
  contract changes were required.
- `test-automator` — checked exact profession and leaf sets, marker count and
  emptiness, removal of shared leaves, and source/configuration scope.
- `reviewer` — independently reviewed naming authority, roster coverage,
  working-tree safety, scope, and validation evidence.

**Final Hero Tree:**

```text
web-ui/public/game-images/heroes/
├── Mage-Comprehensiveness/
├── Paladin-Protection/
├── Paladin-Retribution/
├── Priest-Comprehensiveness/
├── Priest-Discipline/
├── Rogue-Comprehensiveness/
├── Warrior-Defence/
└── Warrior-Weapon-Master/
```

Each profession directory contains:

```text
├── portraits/.gitkeep
├── figures/.gitkeep
├── skills/.gitkeep
└── status-attach/.gitkeep
```

**Files Changed:**

- `web-ui/public/game-images/heroes/**/.gitkeep` — replaced four shared markers
  with 32 profession-specific zero-byte markers.
- `docs/Codex/Completed.md`
- `docs/Codex/Current_Task.md`

**Validation:**

- Exact eight profession directories matched the approved adapter roster.
- Exactly 41 directories exist in the hero subtree: one hero root, eight
  profession directories, and 32 leaf directories.
- Each profession has exactly the four required leaves.
- Exactly 32 `.gitkeep` files exist and every marker is zero bytes.
- No non-marker files or image files exist in the hero subtree.
- The former shared `heroes/portraits`, `heroes/figures`, `heroes/skills`, and
  `heroes/status-attach` directories are absent.
- Non-hero `game-images` branches and existing `game-assets` were preserved.
- No application source, configuration, test, or build file changed.
- `git diff --check` passed.
- No build was run because unreferenced zero-byte public markers cannot affect
  compilation or runtime behavior.

**Naming Decision:**

- The owner explicitly requested title-case faculty-specialization names such
  as `Warrior-Weapon-Master`. That task-specific instruction supersedes
  ASSET-001's general lowercase convention for these profession directories.
- Leaf folders retain lowercase kebab-case, including `status-attach`.

**Unresolved Issues:**

- The UI does not yet resolve assets from the new profession folders and
  continues using `/game-assets/`; wiring remains a separate task.
- The repository contains unrelated, pre-existing local content under
  `docs/ChatGPT/` and an ignored `.DS_Store`. Neither was modified.

**Recommended Follow-up:**

- Define profession asset filenames, required dimensions and formats, and the
  definition-ID-to-directory mapping before populating or wiring these folders.

---

## 2026-07-30 — UI-003: Random Battle Background

**Summary:**

Added a presentation-only registry for the three supplied battle-scene PNGs.
Starting a live battle now selects one background at random, passes it into the
battle screen, and keeps it stable throughout that battle. Returning to Team
Builder clears the selection so the next battle performs a fresh random pick.
The selected image is centered, covers the battlefield, and retains the
existing readability vignette.

**Agent Contributions:**

- `project-manager` — defined the battle-lifecycle boundary, coordinated the
  five roles, protected unrelated working-tree content, and maintained task
  records.
- `ui-developer` — implemented the explicit registry, client-event selection,
  stable BattleScreen presentation state, CSS cover treatment, and architecture
  documentation.
- `game-engine-developer` — confirmed that background randomness is cosmetic
  frontend state and requires no engine, seed, API, or contract change.
- `test-automator` — added deterministic selector and live lifecycle coverage,
  then validated the focused and integrated frontend behavior.
- `reviewer` — reviewed hydration safety, lifecycle stability, accessibility,
  image-loading cost, foreground readability, scope, and final evidence.

**Files Changed:**

- `web-ui/lib/battle/battleBackgrounds.ts`
- `web-ui/components/battle/BattleExperience.tsx`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/app/globals.css`
- `web-ui/tests/battle-backgrounds.test.tsx`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/Codex/Completed.md`
- `docs/Codex/Current_Task.md`
- `web-ui/public/game-images/battle-scenes/backgrounds/*.png` — supplied and
  named by the project owner; consumed without image-content modification.

**Validation:**

- Focused background suite — 7 passed.
- Full frontend Vitest suite — 64 passed across six files.
- TypeScript type checking — passed.
- ESLint — passed.
- Production frontend build — passed; vinext emitted its informational
  route-classification note.
- Live frontend and backend were available on ports 3001 and 8001.
- Browser review started a live battle and confirmed BG03 was selected, its
  computed background used centered `cover`, and the selection stayed unchanged
  after a presentation-speed rerender.
- Browser review confirmed all three public image URLs loaded completely with
  their expected natural dimensions.
- Visual inspection confirmed figures, health bars, target controls, battle
  log, caption, and interface panels remained readable and usable.
- `git diff --check` passed.
- No Python engine, adapter, API model, contract, or test file changed.

**Implementation Decisions:**

- Random selection occurs in the Team Builder Start Battle client event rather
  than during render, preventing server/client hydration mismatch.
- Cosmetic background randomness is deliberately independent from the
  authoritative engine seed.
- Consecutive battles may legitimately select the same image.
- Only the selected image URL is referenced; the implementation does not
  preload all backgrounds.

**Unresolved Issues:**

- The supplied PNGs are approximately 2 MB each and have differing dimensions;
  browser `cover` cropping varies by viewport. Image optimization remains a
  separate asset-production task.
- The fixed `THE FALLEN CITADEL` caption may not describe every future
  background if the scene library expands.

**Recommended Follow-up:**

- Define an optimized production background format and responsive variants
  before adding a larger scene library.

---

## 2026-07-30 — UI-004: Raise 1v1 Battlefield Health Bars

**Summary:**

Raised the battlefield health/status panels only in the 1v1 duel layout to add
clearance above the enlarged hero figures. The duel offset changed from the
shared `top: -5px` position to `top: -20px`; 2v2 and 3v3 retain the original
shared offset.

**Agent Contributions:**

- `project-manager` — constrained the change to duel presentation, coordinated
  validation and documentation, and protected the existing dirty worktree.
- `ui-developer` — implemented the single duel-only CSS override and performed
  live visual and computed-style inspection.
- `game-engine-developer` — confirmed the existing `format-duel` marker is the
  correct boundary and that no formation, engine, API, or contract change was
  required.
- `test-automator` — reviewed the format-scoped selector and regression plan,
  and verified integrated frontend validation evidence.
- `reviewer` — independently reviewed the offset, 1v1 clearance, unchanged
  duo/trio geometry, accessibility, scope, and final evidence.

**Files Changed:**

- `web-ui/app/globals.css`
- `docs/web-ui/Style_Guide.md`
- `docs/Codex/Completed.md`
- `docs/Codex/Current_Task.md`

**Validation:**

- Live computed styles: both 1v1 overheads resolved to `top: -20px`.
- Live computed styles: all four 2v2 overheads and all six 3v3 overheads
  remained `top: -5px`.
- Live 1v1 screenshot inspection confirmed improved clearance on both sides,
  readable health panels, and no battlefield-edge clipping.
- Figures, formation anchors, target controls, and health/status content were
  not changed.
- Full frontend Vitest suite — 64 passed across six files.
- TypeScript type checking — passed.
- ESLint — passed.
- Production frontend build — passed; vinext emitted its informational
  route-classification note.
- `git diff --check` passed.
- No Python, adapter, API, battle-contract, formation-registry, or test file
  changed.

**Unresolved Issues:**

- The adjustment was validated at the currently supported live desktop layout;
  future changes to duel figure scale should recheck this spacing.

**Recommended Follow-up:**

- No further action is required unless owner review requests a different duel
  clearance after hero figure artwork replaces placeholders.

---

## 2026-07-31 — UI-003: Investigate Stun and Scoff Action Restrictions

**Summary:**

Completed a five-role, documentation-only investigation of the original Python
and live web-integration paths for Shield Bash Stun and Shield Lash/Heroric
Charge Scoff. Current controlled real-skill scenarios did not reproduce the
reported action-legality failures: Stun skipped the restricted turn, and Scoff
automatically attacked its initiator for both player- and computer-controlled
targets. The study records the remaining architectural risks and an
implementation-ready engine-owned turn-directive design without marking the
reported defect fixed.

**Agent Contributions:**

- `project-manager` — enforced the no-fix boundary, coordinated all five roles,
  consolidated evidence, and maintained task records.
- `ui-developer` — traced live-provider, legal-action, interaction,
  presentation-queue, and final-snapshot reconciliation behavior.
- `game-engine-developer` — traced and reproduced legacy Game, Hero, skill,
  status-duration, forced-target, and adapter behavior using actual skills.
- `test-automator` — ran controlled player/computer scenarios, assessed current
  automated coverage, and designed the proposed regression matrix.
- `reviewer` — independently reproduced the public-adapter happy path and
  reviewed root-cause claims, architecture, scope, and unresolved semantics.

**Files Changed:**

- `docs/Codex/Analysis/UI_003_Action_Restriction_Integration_Study.md`
- `docs/Codex/Completed.md`
- `docs/Codex/Current_Task.md`

**Validation:**

- Focused adapter Stun/Scoff tests — 6 passed, 39 deselected.
- Controlled engine and adapter experiments used real Shield Bash, Shield Lash,
  and Heroric Charge skills for player- and computer-controlled targets; the
  expected automatic restrictions were observed.
- Full Python suite — 59 passed with one Starlette deprecation warning.
- Relevant frontend suites — 38 passed.
- Full frontend suite — 64 passed across six files.
- TypeScript type checking, ESLint, and the production web build — passed.
- Owner-controlled review-file SHA-256 was unchanged at
  `5c93e620ae0cd28ce0f48885bede782e94686d1ec6fe20d5c4bcc121725e78d3`.
- Task-scoped Markdown whitespace validation passed. Repository-wide
  `git diff --check` reports pre-existing trailing whitespace in the
  owner-controlled review file; it was preserved rather than edited.
- No production behavior was changed by UI-003.

**Unresolved Issues:**

- The owner's symptom is not reproducible on the current happy path; a precise
  current seed/runtime scenario is needed to identify whether stale processes,
  evasion/immunity, initiative timing, or transient presentation caused the
  observation.
- The adapter duplicates engine restriction decisions and the API lacks
  explicit turn-control semantics.
- Scoff source identity is not serialized, command validation lacks an
  independent control-boundary check, and frontend automatic-turn presentation
  is incomplete.
- Duration-one Stun has timing-sensitive legacy round-boundary behavior that
  requires owner confirmation before any implementation changes it.

**Recommended Follow-up:**

- After owner decisions on Stun duration, contract versioning, automatic-turn
  presentation, and no-legal-attack Scoff behavior, authorize a separate
  implementation task for an engine-owned turn directive, explicit contract
  control state, strict adapter validation, and end-to-end regressions.

---

## 2026-07-31 — UI-005: Authoritative Action-Restriction Integration

**Summary:**

Implemented the UI-003 study recommendations as a backward-compatible v1
integration. Python now produces a shared turn directive for player commands,
automatic actions, skipped turns, and battle completion. The legacy Game and
web adapter consume this authority, the adapter strictly rejects commands at
restricted boundaries, and snapshots expose explicit `turnControl` plus status
source identity. React gates all controls on that explicit boundary and
presents automatic and skipped turns from authoritative events without
interpreting gameplay statuses.

Shield Bash Stun and Shield Lash/Heroric Charge Scoff are covered through real
skill execution for player- and computer-controlled targets. Existing Stun
duration, Scoff targeting/fallback, combined-status precedence, seeded session
behavior, and the engine spelling `Heroric Charge` were preserved.

**Agent Contributions:**

- `project-manager` — defined the backward-compatible implementation
  assumptions, coordinated the five roles, resolved scope and precedence
  findings, maintained documentation, and managed final live validation.
- `ui-developer` — added typed turn-control semantics, authoritative
  interaction gating, transient actor/status reconciliation, skip feedback,
  and mock-provider parity.
- `game-engine-developer` — implemented `TurnDirective`, refactored Game and
  adapter consumption, added source serialization and strict validation, and
  preserved legacy combined-status and forced-action behavior.
- `test-automator` — added actual-skill backend integration and frontend
  control/presentation regressions and ran the complete automated gate.
- `reviewer` — independently identified and verified fixes for precedence,
  status consumption, forced-skill compatibility, source events, skip
  presentation, canonical IDs, deterministic test assertions, and scope.

**Files Changed:**

- `heroes/hero.py`
- `game/game.py`
- `battle_api/adapter.py`
- `tests/test_battle_adapter.py`
- `tests/test_action_restrictions_integration.py`
- `web-ui/lib/battle/types.ts`
- `web-ui/lib/battle/fixture.ts`
- `web-ui/lib/battle/usePresentationQueue.ts`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/tests/action-restrictions.test.tsx`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`
- `docs/web-ui/PYTHON_ADAPTER_API.md`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`

**Validation:**

- Python compilation — passed for engine, adapter, and changed backend tests.
- Full Python suite — 75 passed; one existing Starlette deprecation warning.
- Focused restriction/dead-source backend suite — 11 passed.
- Full frontend Vitest suite — 68 passed across seven files.
- TypeScript type checking — passed.
- ESLint — passed.
- Production frontend build — passed; vinext emitted its informational
  route-classification note.
- Task-scoped `git diff --check` and new-file whitespace checks — passed.
- Independent reviewer — approved with no remaining blocker.
- Owner-controlled review-file SHA-256 remained
  `5c93e620ae0cd28ce0f48885bede782e94686d1ec6fe20d5c4bcc121725e78d3`.
- Restarted frontend on port 3001 and backend on port 8001; roster, battle
  creation, and frontend HTTP requests returned 200.
- Live 1v1 browser validation cast Shield Bash: the log showed Stun application,
  Nighthawk's restricted turn ending without a skill, and controls returning
  to Aegis.
- Live 1v1 browser validation then cast Shield Lash: after Stun expired,
  Nighthawk automatically used Sharp Blade against Aegis, Scoff was removed,
  and no player-control prompt appeared for the forced action.

**Implementation Decisions:**

- `turnControl` is an additive v1 field; no contract version was introduced.
- Existing Stun duration and combined-status precedence were not redesigned.
- Scoff retains the legacy off-cooldown attack selection, including its
  existing availability behavior and two-target fallback.
- React uses `turnControl` and published `legalActions`; it does not inspect
  status names to determine command ownership.
- Direct private-drain test assertions accept the selected AI skill's valid
  target shape instead of depending on module-global random history.

**Unresolved Issues:**

- Frontend and backend must be deployed together because the updated frontend
  requires the additive `turnControl` field.
- The process-local adapter still has the documented single-worker and
  persistence limitations.
- The existing Starlette test-client deprecation warning remains.

**Recommended Follow-up:**

- Have the project owner verify Shield Bash, Shield Lash, and Heroric Charge in
  the restarted live UI. Any requested change to Stun duration or Scoff's
  no-attack edge remains a separate game-design decision.

---

## 2026-07-31 — BUG-001: Make Evaded Attacks Suppress Harmful Target Effects

**Summary:**

Investigated the reported Shield Bash evade-plus-Stun behavior across the
engine, adapter, and web event path. A true engine evade already excluded its
target from the skill callback, so Shield Bash and the audited harmful-effect
skills did not mutate an evading target. The reproducible defect was instead a
false adapter event: any landed damage skill that left HP unchanged was
reported as `attackEvaded`. A zero-damage Shield Bash could therefore correctly
apply Stun while the UI incorrectly said that the attack was evaded.

The engine now records an authoritative outcome for every resolved target, and
the adapter uses that outcome rather than inferring evasion from HP. This fixes
the observed contradiction systematically for current and future skills,
including independent outcomes in multi-target attacks. Target-side skill
callbacks remain hit-gated.

The former name-specific miss handling for five mixed-effect attacks was
replaced by an optional independent-benefit callback. Crusader Strike, Shield
of Righteous, Heroric Charge, Cumbrous Axe, and Shield Lash now declare their
caster benefits explicitly, so those benefits remain independent of whether
the harmful target attack lands. Existing control-immunity behavior was
preserved.

**Agent Contributions:**

- `project-manager` — established the authoritative task, coordinated the
  five-role investigation, reconciled the reported symptom with engine and
  adapter evidence, and maintained the documentation workflow.
- `ui-developer` — traced the event-to-presentation path and confirmed that the
  frontend already renders the semantic events correctly, so no React change
  was required.
- `game-engine-developer` — audited the shared resolution paths, added
  authoritative per-target outcomes and the independent-benefit seam, migrated
  all five known mixed-effect attacks, and corrected independent buff source
  serialization.
- `test-automator` — added deterministic hit, evade, zero-damage, mixed-benefit,
  and multi-target regressions; exposed and retested the Shield Lash
  serialization edge; and ran the complete automated gate.
- `reviewer` — independently confirmed the actual root cause, audited harmful
  effect gating, identified the control-immunity compatibility requirement,
  and reviewed the systematic boundary and final evidence.

**Files Changed:**

- `skills/skill.py`
- `heroes/hero.py`
- `heroes/paladin.py`
- `heroes/warrior.py`
- `heroes/death_knight.py`
- `battle_api/adapter.py`
- `tests/test_evasion_effect_boundaries.py`
- `docs/GDD/Combat_System.md`
- `docs/GDD/Skill_System.md`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`
- `docs/Codex/Completed.md`
- `docs/Codex/Current_Task.md`

**Validation:**

- Deterministic regression coverage confirms that a landed Shield Bash applies
  Stun, a true evade applies neither damage nor Stun, and a landed zero-damage
  Shield Bash applies Stun without producing `attackEvaded`.
- All five registered mixed-effect attacks retain their independent caster
  benefit when their target evades.
- A real multi-target execution records and gates hit and evade outcomes
  independently.
- Control-immunity regressions preserve no-Scoff behavior plus the historical
  independent benefit and cooldown for Heroric Charge, Cumbrous Axe, and
  Shield Lash, including Shield Lash's existing resistance sequence.
- Full Python suite — 87 passed; one existing Starlette deprecation warning.
- Python compilation — passed.
- Full frontend Vitest suite — 68 passed.
- TypeScript type checking, ESLint, and the production frontend build — passed.
- The frontend required no production change for BUG-001.
- Restarted the backend on port 8001; its health endpoint and the existing
  frontend on port 3001 both returned HTTP 200.
- Task-scoped whitespace checks passed. Repository-wide `git diff --check`
  reports only pre-existing trailing whitespace in the owner-controlled human
  review file, which was preserved.
- Owner-controlled review-file SHA-256 remained
  `5c93e620ae0cd28ce0f48885bede782e94686d1ec6fe20d5c4bcc121725e78d3`.

**Unresolved Issues:**

- Shield Lash retains its legacy control-immunity behavior, including its
  existing independent-effect resolution sequence. Any balance or
  normalization change to that behavior requires a separate approved task.
- The existing Starlette test-client deprecation warning remains.

**Recommended Follow-up:**

- Add an explicit typed outcome model if future consumers require more detail
  than the current internal per-target outcome categories. No additional
  evade-specific skill patch is required.

---

## 2026-07-31 — OPS-001: Restore the Local Game Website and Verify the Live Battle Flow

**Summary:**

Restored the local website and battle API by starting the two documented
development services. Both ports had immediate connection refusals before
recovery, and both applications started normally without a code or
configuration change. The confirmed root cause was therefore stopped local
development processes, not an application regression.

The frontend is running at `http://localhost:3001/` and the Python adapter is
running at `http://localhost:8001`. The frontend development server listens on
the IPv6 localhost address (`::1`), while Uvicorn listens on
`127.0.0.1`; both documented `localhost` URLs work.

**Agent Contributions:**

- `project-manager` — coordinated recovery, protected the dirty worktree and
  owner-controlled files, kept diagnosis conditional on startup failure, and
  completed the documentation workflow.
- `ui-developer` — started `npm run dev`, inspected startup output, verified
  live-provider configuration and CORS, and completed the rendered Team Builder
  through battle-action browser flow. No frontend change was required.
- `game-engine-developer` — started the documented Uvicorn reload process and
  verified health, roster, 1v1 creation, legal command handling, revision
  advancement, and clean backend logs. No backend change was required.
- `test-automator` — independently repeated HTTP, roster, CORS, battle-create,
  and command-submission checks and confirmed the localhost IPv6 binding.
- `reviewer` — independently confirmed both listeners and HTTP endpoints,
  reviewed the live-flow evidence and repository status, verified owner-file
  protection, and approved completion with no blockers.

**Files Changed:**

- `docs/Codex/Completed.md`
- `docs/Codex/Current_Task.md` (assigned task reset to the standard placeholder)

No application, test, configuration, package, or asset file changed.

**Recovery Commands:**

- Backend from the repository root:
  `.venv/bin/uvicorn battle_api.app:app --reload --port 8001`
- Frontend from `web-ui/`: `npm run dev`

**Validation:**

- Pre-recovery frontend, health, and roster probes returned HTTP `000` with
  immediate connection refusal.
- Backend startup completed under the Uvicorn reload process with no exception.
- Frontend startup reported `http://localhost:3001/` and served the root with
  HTTP `200`.
- `GET /api/v1/health` — HTTP `200`, status `ok`, contract version `1.0`.
- `GET /api/v1/heroes` — HTTP `200` with exactly the eight approved heroes.
- CORS GET and OPTIONS checks — HTTP `200`, exact allowed origin
  `http://localhost:3001`, and the documented methods/headers.
- Direct live 1v1 creation — HTTP `200`, authoritative revision `0` with
  published legal actions.
- Direct published command — HTTP `200`, accepted, revision advanced from `0`
  to `1`, and the next actor exposed legal actions.
- Isolated browser smoke — Team Builder rendered all eight heroes; a live 1v1
  battle rendered; Holy Smite and its legal enemy target were selected and
  submitted; damage and turn events played; the screen reconciled to the next
  actionable player state with enabled skills.
- Instrumented browser repeat — no console errors, uncaught errors, unhandled
  promise rejections, or alert-state failures were captured.
- Backend request log contained no exception during the verified flow.
- Independent reviewer approved with no blockers.
- Owner-controlled `UI_Review_Human.md` SHA-256 remained
  `5c93e620ae0cd28ce0f48885bede782e94686d1ec6fe20d5c4bcc121725e78d3`.

**Unresolved Issues:**

- These are development processes and must be restarted after they stop or the
  host restarts.
- The frontend currently binds to IPv6 localhost, so
  `http://127.0.0.1:3001/` is not equivalent to the documented working
  `http://localhost:3001/` address.
- The adapter registry remains process-local and limited to one worker.

**Recommended Follow-up:**

- Continue using `http://localhost:3001/` for the website and keep both
  documented development commands running during local testing. No repository
  implementation follow-up is required for OPS-001.

---

## 2026-07-31 — UI-006: Refine Battlefield Layout, Python-Authored Battle Logs, Hero Identity, and Skill Cards

**Summary:**

Implemented all seven owner-approved corrections from
`battle_31_07_2026-01`. Duel, duo, and trio formation anchors now place hero
figures lower on the arena floor. Battle Log typography is larger, and the log
now presents ordered, ANSI-sanitized lines emitted by Python through
`display_battle_info()` and `display_status_updates()` without parsing prose
for state. Typed semantic events continue to drive animation and snapshot
reconciliation; covered generic copies are hidden to prevent duplicate lines.

Battle side cards now show faculty plus specialization. Non-summoned battle
names are chosen from the authoritative `HeroGenerator` faculty pools across
both teams, remain unique until the faculty pool is exhausted, reproduce under
the session seed, and do not change stable definition or combatant IDs. Name
selection derives from and restores the seeded stream before hero construction
so existing stat and combat rolls are not shifted.

Skill cards now fill the command-deck height with square artwork and an
intentional decorative lower treatment. Player Team selectors show
`Faculty - Specialization` while preserving stable definition IDs; specified
Enemy Team selectors retain their existing catalogue-name presentation.

**Agent Contributions:**

- `project-manager` — completed the required documentation startup, protected
  the owner-controlled review inputs and existing worktree changes, coordinated
  all five roles, reconciled the faculty-pool overflow result, maintained the
  authoritative documentation, and closed the task workflow.
- `ui-developer` — implemented shared formation anchors, readable Battle Log
  styling, complete profession labels, full-height skill cards with square
  artwork, player-slot labels, typed presentation-log handling, and live
  1v1/2v2/3v3 browser validation at the annotated viewport.
- `game-engine-developer` — added ordered presentation-log capture, sanitized
  additive adapter events, duplicate-copy visibility metadata, deterministic
  faculty-pool runtime naming, stable-ID preservation, and explicit
  faculty-wide uniqueness bookkeeping.
- `test-automator` — added backend and frontend UI-006 regressions, updated
  invalidated presentation assertions, made affected control-immunity tests
  deterministic, and added the public-adapter real-round transition regression
  requested during review.
- `reviewer` — independently audited Python authority, typed state/event
  reconciliation, identity and RNG boundaries, queue/skip behavior,
  accessibility, responsive layout, tests, live evidence, and owner-file
  hashes; identified the missing integrated round-transition proof and approved
  the corrected result with no blockers.

**Files Changed:**

- `game/game.py`
- `battle_api/adapter.py`
- `web-ui/app/globals.css`
- `web-ui/components/battle/BattleScreen.tsx`
- `web-ui/components/battle/HeroCard.tsx`
- `web-ui/components/battle/SkillCard.tsx`
- `web-ui/components/battle/TeamBuilder.tsx`
- `web-ui/lib/battle/formations.ts`
- `web-ui/lib/battle/types.ts`
- `web-ui/lib/battle/usePresentationQueue.ts`
- `tests/test_battle_adapter.py`
- `tests/test_evasion_effect_boundaries.py`
- `tests/test_ui006_identity_and_logs.py`
- `web-ui/tests/battle-screen.test.tsx`
- `web-ui/tests/components.test.tsx`
- `web-ui/tests/stage-two-automation.test.tsx`
- `web-ui/tests/ui-006-refinements.test.tsx`
- `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`
- `docs/web-ui/PYTHON_ADAPTER_API.md`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/web-ui/Screen_Flow.md`
- `docs/web-ui/Style_Guide.md`
- `docs/Codex/Completed.md`
- `docs/Codex/Current_Task.md` (assigned task reset to the standard placeholder)

**Validation:**

- Full Python suite — 96 passed; one existing Starlette deprecation warning.
- UI-006 backend suite — 9 passed.
- The integrated public-adapter round-transition regression submitted real
  commands through Round 2 and verified sanitized ordered `statusUpdate` prose,
  unique event sequences, retained typed mutations, hidden duplicate copies,
  and no duplicate status lines.
- Full frontend Vitest suite — 74 passed.
- UI-006 frontend suite — 6 passed.
- TypeScript type checking, ESLint, and the production frontend build — passed.
- Python compilation and task-scoped whitespace checks — passed.
- Live 1v1 at 1468×799 submitted a Python-authorized Holy Smite command; the
  ordered engine prose contained no ANSI sequences or raw IDs, typed state
  reconciled, Battle Log text computed to 11px, skill cards filled the 179px
  skills region, artwork was 44×44, and no console or unhandled errors appeared.
- A second live 1v1 used Shadow Evasion and reached Round 2 with ordered
  cooldown and status-duration lines from Python and no browser errors.
- Live 2v2 confirmed faculty-wide naming: four Priests consumed all three
  unique Priest names before the fourth valid overflow repeat.
- Live 3v3 confirmed six distinct figure rectangles with no overlap, grounded
  formation anchors, 11px Battle Log text, complete profession labels, and
  full-height square-artwork skill cards.
- Independent review reran the UI-006 backend suite (9 passed), frontend suite
  (6 passed), and annotated-viewport browser inspection; verdict approved with
  no blockers.
- Repository-wide `git diff --check` reports only the pre-existing trailing
  whitespace in the owner-controlled human review file, which was not edited.
- Owner-controlled SHA-256 baselines remained unchanged:
  `UI_Review_Human.md` `49a1ba65efa2846a255cb9cd4a13fe805bf34d4e4dbef9a87edfa8e577697e20`,
  screenshot `0e180499bf950232dafaa1ea0eb91b0b2efd7c1a5cacdd874b8585c076562378`,
  and Keynote `affce7c7fd3c2eaf333c8e2d4017e38276ce456d5b28d12fcdcfccd7a86c89ee`.

**Unresolved Issues:**

- Duplicate semantic-log suppression currently applies to a fixed action-wide
  event set whenever Python emitted presentation prose, rather than correlating
  each prose line to one semantic event. The approved roster, automated tests,
  and live flows have complete prose coverage, so this is non-blocking future
  hardening rather than a UI-006 defect.
- The process-local adapter's documented single-worker and persistence limits
  remain.
- The existing Starlette test-client deprecation warning remains.

**Recommended Follow-up:**

- If future skills emit only partial presentation prose for a multi-effect
  action, add explicit prose-to-semantic-event correlation metadata before
  expanding the suppression set. No additional UI-006 implementation is
  required.

---

## 2026-07-31 — Update the Agent Cooperation Rule to Proportional Assignment

**Summary:**

Replaced the mandatory participation rule with a proportional agent-selection
workflow. The project manager now assesses every task's type, affected systems,
complexity, risk, and validation needs before assigning one or more relevant
configured agents. Agent breadth increases with task complexity.

Official tasks assigned through `docs/Codex/Current_Task.md` still normally use
all five agents, with bug fixes strongly defaulting to all five. A narrower
official assignment is permitted only when the project manager records why
each omitted role is unnecessary. Non-participating agents no longer perform
artificial no-change assessments merely to satisfy a participation count.

**Agent Selection and Contributions:**

- Complexity/risk assessment — documentation-governance change with no
  application, engine, API, frontend, or test behavior impact. Cross-document
  consistency was the primary risk.
- `project-manager` — selected the proportional team, located every active
  mandatory-five rule, updated the authoritative workflow documents and task
  template, preserved historical records, and validated the final wording.
- `reviewer` — independently checked the five scoped workflow documents,
  identified two completion clauses that still implied mandatory reviewer
  participation, and approved the corrected policy with no blockers.
- `ui-developer` — not selected because no frontend behavior or web UI
  documentation changed.
- `game-engine-developer` — not selected because no engine, adapter, API, or
  contract behavior changed.
- `test-automator` — not selected because this was a Markdown-only policy
  update with no executable behavior; targeted consistency and Markdown checks
  were proportionate validation.

**Files Changed:**

- `docs/README.md`
- `docs/Codex/Project_Rules.md`
- `docs/Codex/Agent_Roles.md`
- `docs/Codex/Document_Planner_Rules.md`
- `docs/Codex/Current_Task.md`
- `docs/Codex/Completed.md`

**Validation:**

- Searched active workflow documents for contradictory mandatory-five,
  all-five-assignment, artificial no-change, and unconditional-reviewer rules;
  no contradiction remains.
- Task-scoped `git diff --check` — passed.
- Independent reviewer re-read all five scoped workflow documents after the
  correction and approved the result with no blockers.
- Historical completion and UI-review records were preserved rather than
  rewritten to reflect a policy that did not apply when those tasks ran.
- Owner-controlled review inputs remained unchanged at their confirmed
  SHA-256 baselines: `49a1ba65...`, `0e180499...`, and `affce7c7...`.

**Unresolved Issues:**

- None for this policy update. Future project managers must exercise judgment
  consistently when classifying task complexity and documenting narrower
  official-task assignments.

**Recommended Follow-up:**

- Apply this proportional selection step at the beginning of every new task.
  Continue to default official bug-fix tasks to all five roles unless a clearly
  documented scope and risk assessment justifies fewer.

---

## 2026-08-01 — Apply the Paladin Protection Figure in Live Battles

**Summary:**

Registered the owner-provided Paladin Protection figure against the stable
`hero.paladin.protection` definition. The real artwork now appears for Paladin
Protection combatants in live battles. Friendly-side artwork preserves its
original orientation, while enemy-side artwork is horizontally mirrored.

The mirror transform is restricted to requested battlefield image pixels. It
does not transform formation movement, overhead health/status UI, labels,
auras, target controls, side cards, portraits, or thumbnails. Final figure art
uses contained, bottom-aligned presentation without the placeholder silhouette
clip, and missing assets continue to use the established fallback behavior.

Initial live validation exposed a Vinext optimizer HTTP 400 that replaced both
figures with initials. Repository-native `/game-images/` sources now bypass the
optimizer and use their direct public URL; other image paths retain their
existing behavior, and genuine load failures still fall back safely.

**Agent Selection and Contributions:**

- Complexity/risk assessment — focused frontend asset registration and visual
  orientation behavior with a runtime loading risk; no engine or API contract
  change.
- `project-manager` — inspected the supplied asset and current registry,
  assigned frontend implementation and test ownership, coordinated resolution
  of the live optimizer failure, and updated authoritative documentation.
- `ui-developer` — registered the definition-ID asset, added final-art
  containment and enemy-only mirroring, and implemented direct static loading
  for repository-native game images.
- `test-automator` — added asset/rendering regressions, ran the full frontend
  gates, and completed live friendly-versus-enemy Paladin validation with DOM,
  computed-style, resource, and browser-error evidence.
- `game-engine-developer` — not selected because hero identity, game rules,
  adapter output, and API contracts were unchanged.
- `reviewer` — not selected because this narrow non-official frontend task had
  focused automated coverage plus successful live validation; an additional
  independent review was not proportionate to its residual risk.

**Files Changed:**

- `web-ui/lib/battle/assets.ts`
- `web-ui/components/battle/AssetImage.tsx`
- `web-ui/app/globals.css`
- `web-ui/tests/paladin-protection-figure.test.tsx`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/web-ui/Style_Guide.md`
- `docs/Codex/Completed.md`

The source image at
`web-ui/public/game-images/heroes/Paladin-Protection/figures/Paladin_Protection.png`
was supplied by the project owner and already present in repository history.

**Validation:**

- Focused Paladin figure tests — 2 passed.
- Full frontend Vitest suite — 76 passed across 9 files.
- TypeScript type checking, ESLint, production build, and task-scoped
  `git diff --check` — passed.
- Live Python-backed 1v1 used Paladin Protection on both sides. Friendly Bors
  and enemy Percival both rendered decoded image elements using the direct
  `/game-images/heroes/Paladin-Protection/figures/Paladin_Protection.png` URL.
- Direct asset request — HTTP 200, `image/png`, 2,926,130 bytes; no optimizer
  route or fallback artwork was used.
- Friendly computed transform — `none`; enemy computed transform —
  `matrix(-1, 0, 0, 1, 0, 0)`.
- Overhead panels, figure labels, and target buttons remained untransformed;
  both HP panels rendered correctly.
- No console, runtime, network, API, or asset-loading errors were recorded.
- The live screenshot command timed out, but DOM, decoded-image, computed-style,
  resource-timing, direct-fetch, and semantic evidence all completed
  successfully. The isolated browser task space closed cleanly.

**Unresolved Issues:**

- None for the requested Paladin Protection figure integration.

**Recommended Follow-up:**

- Register future final battlefield figures by stable definition ID under the
  same `/game-images/` convention so they receive consistent containment,
  fallback, and enemy-orientation behavior.

---

## 2026-08-01 — Apply Five Supplied Final Hero Figures in Live Battles

**Summary:**

Extended the final battlefield-figure registry to use the owner-supplied art
for Paladin Protection, Paladin Retribution, Priest Comprehensiveness, Warrior
Defence, and Warrior Weapon Master. Each mapping uses the stable hero
definition ID, not a runtime display name. All final images use direct public
`/game-images/` URLs, original orientation on the player side, and enemy-only
horizontal mirroring limited to artwork pixels.

**Agent Selection and Contributions:**

- Complexity/risk assessment — focused frontend asset-registration expansion
  with repeated live rendering and asset-path validation; no engine, API, or
  game-rule change.
- `project-manager` — inspected all supplied image paths, identified the
  trailing-space Paladin Protection folder, preserved owner files, assigned the
  focused UI and QA work, and updated the authoritative documentation.
- `ui-developer` — registered all five stable definition IDs with their exact
  direct figure URLs, retained existing direct-static loading, and preserved
  enemy-only mirror behavior.
- `test-automator` — expanded deterministic asset/rendering regressions and
  completed five live configured 1v1 browser validations covering each player
  and enemy figure.
- `game-engine-developer` and `reviewer` — not selected because this narrow
  presentation-only asset task changed no authoritative state, contract, or
  higher-risk cross-system behavior.

**Files Changed:**

- `web-ui/lib/battle/assets.ts`
- `web-ui/tests/paladin-protection-figure.test.tsx`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/Codex/Completed.md`

**Validation:**

- Focused final-figure tests — 12 passed.
- Full frontend Vitest suite — 86 passed across 9 files.
- TypeScript type checking, ESLint, production build, and task-scoped
  `git diff --check` — passed.
- Five live 1v1 browser runs used each final figure as both player and specified
  enemy: Paladin Protection, Paladin Retribution, Priest Comprehensiveness,
  Warrior Defence, and Warrior Weapon Master.
- Every side rendered a complete image element from its expected direct
  `/game-images/.../figures/*.png` URL; no fallback artwork or optimizer route
  appeared.
- Friendly artwork computed to `transform: none`; enemy artwork computed to
  `matrix(-1, 0, 0, 1, 0, 0)`. Labels, overhead panels, and target controls
  remained untransformed.
- No console, runtime, log, or network errors appeared. The browser task space
  closed cleanly.

**Unresolved Issues:**

- The owner-supplied Paladin Protection directory is currently named
  `Paladin-Protection ` with a trailing space. Its working public URL encodes
  this as `Paladin-Protection%20`; the files were deliberately not renamed.

**Recommended Follow-up:**

- If the owner approves an asset-folder normalization, move Paladin Protection
  back to `Paladin-Protection/` in one dedicated asset-maintenance task and
  update the registry URL. No runtime issue exists while the encoded path is
  retained.

---

## 2026-08-01 — Normalize the Paladin Protection Asset Folder and Figure URL

**Summary:**

At the owner's request, renamed the supplied Paladin Protection asset directory
from `Paladin-Protection ` to `Paladin-Protection`, removing its trailing
space. The figure registry now uses the clean direct public URL:
`/game-images/heroes/Paladin-Protection/figures/Paladin_Protection.png`.

All source-directory contents were preserved, including the final PNG and the
existing `.gitkeep` and `.DS_Store` files. Friendly and enemy figure behavior
is unchanged: player artwork remains original and enemy artwork is mirrored.

**Agent Selection and Contributions:**

- Complexity/risk assessment — narrow owner-authorized filesystem rename plus
  frontend path remap, with asset-load regression risk but no engine or API
  impact.
- `project-manager` — confirmed the source/target paths before the rename,
  ensured the target was absent, coordinated exact-path validation, and updated
  authoritative documentation.
- `ui-developer` — performed the precise directory rename, remapped the stable
  Paladin Protection definition URL, and verified static asset loading and the
  frontend build.
- `test-automator` — updated exact-path regression coverage and confirmed the
  clean URL in focused tests and a live player-versus-enemy battle.
- `game-engine-developer` and `reviewer` — not selected because no game rule,
  adapter/API contract, or broader cross-system behavior changed.

**Files Changed:**

- `web-ui/public/game-images/heroes/Paladin-Protection/`
- `web-ui/lib/battle/assets.ts`
- `web-ui/tests/paladin-protection-figure.test.tsx`
- `docs/web-ui/WEB_UI_ARCHITECTURE.md`
- `docs/Codex/Completed.md`

**Validation:**

- Focused final-figure suite — 12 passed.
- Full frontend suite — 86 passed on isolated rerun. An earlier concurrent run
  had one unrelated Stage Two timing failure before an isolated rerun passed;
  no figure-path regression was found.
- TypeScript type checking, ESLint, production build, and task-scoped
  `git diff --check` — passed.
- Live configured 1v1 used Paladin Protection on both player and specified
  enemy sides. Both complete images used the exact clean direct URL without a
  fallback or optimizer route.
- Friendly computed transform — `none`; enemy computed transform —
  `matrix(-1, 0, 0, 1, 0, 0)`. Labels, overhead UI, and target controls were
  unchanged, and no browser console, runtime, or log errors occurred.

**Unresolved Issues:**

- None for the folder normalization or figure remap.

**Recommended Follow-up:**

- Use the normalized `Paladin-Protection/` convention for future related
  portrait, skill, and status assets.

---

## 2026-08-01 — Add Root `make dev` Local Development Launcher

**Summary:**

Added a root `Makefile` so `make dev` starts the existing Python adapter on
port 8001 and web client on port 3001 together. The recipe retains separate
`make backend` and `make frontend` targets for focused local work and traps
Ctrl-C/termination to stop the two launched child processes.

**Agent Selection and Contributions:**

- Complexity/risk assessment — small local-development tooling change with
  process-lifecycle and port-availability risk, but no game, API, or frontend
  behavior change.
- `project-manager` — confirmed the previous root launcher was absent, added
  the focused Make targets, documented the supported command, and preserved
  existing port assignments.
- `test-automator` — selected to validate the combined process launcher,
  frontend/backend reachability, and shutdown behavior.
- `ui-developer`, `game-engine-developer`, and `reviewer` — not selected
  because no UI, game/API contract, or high-risk cross-system change was made.

**Files Changed:**

- `Makefile`
- `docs/web-ui/PYTHON_ADAPTER_API.md`
- `docs/Codex/Completed.md`

**Validation:**

- `make -n dev`, `make -n backend`, and `make -n frontend` produced the
  expected adapter and frontend commands.
- With ports 3001 and 8001 free, `make dev` started the Uvicorn reloader and
  frontend development server successfully.
- `GET http://127.0.0.1:8001/api/v1/health` — HTTP 200.
- `GET http://127.0.0.1:3001/` — HTTP 200.
- One controlled Ctrl-C stopped the Makefile session with exit 130; neither
  port remained listening afterward, so no child-process or reloader listener
  leak was observed.
- Task-scoped `git diff --check` — passed.

**Unresolved Issues:**

- None known; the launcher requires the existing Python virtual environment and
  frontend dependencies to be installed.
