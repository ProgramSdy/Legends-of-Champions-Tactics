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
