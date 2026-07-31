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
