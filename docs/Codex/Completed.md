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

**Completed:** 2026-07-25 (inferred from file timestamps and the completion
report; the work is currently present in the working tree rather than a
dedicated Git commit)

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
