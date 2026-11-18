# RELEASE-001 / Task A — Engineering Test Production Isolation Implementation

**Date:** 2026-11-10 (Australia/Sydney)
**Scope:** Application/build isolation only; no deployment, combat-rule, seed-policy, identity, or persistence change.
**Source decision:** `docs/Codex/Current_Task.md` and the completed `docs/Codex/Engineering_Test_Production_Isolation_Audit.md`.

## 1. Executive Summary

The repository now has explicit Development and Public Release modes selected by `LOCT_RELEASE_MODE`. The frontend's Public build omits the `/debug` Engineering Test and `/assets` Asset Diagnostics route directories from a disposable source copy **before vinext route discovery**, checks the generated artifact for excluded route/page code, and marks the verified artifact. Public `npm start` checks that marker and artifact again before serving. The backend registers its debug battle-creation router only in explicit Development mode, so Public and missing/invalid mode have neither that route nor its OpenAPI path. Normal gameplay still uses the same Team Builder, Battle Screen, adapter, engine, asset registry, and progression store.

This is an application release boundary, **not** a declaration that the game is ready for open Internet use. Authentication, save-slot ownership, abuse limits, production ingress/TLS, and public-player seed restriction remain separate release work.

## 2. Approved Release Policy

| Surface | Explicit Development | Public Release and missing/invalid mode |
| --- | --- | --- |
| `/debug`, `/assets` | Built and directly navigable | Omitted from Public frontend route discovery and resulting artifact; direct paths must 404 |
| Stage Map Engineering link / hotspot overlay | Available, with `?debugHotspots=1` for the overlay | Link absent; query cannot enable overlay |
| Battle viewport/configuration readout | Visible | Hidden |
| `POST /api/v1/debug/battles` | Registered; full-roster, deterministic no-save test battle | Not registered; absent from OpenAPI; direct POST 404 |
| Shared game, health, ordinary API routes | Available | Available |

The exact `development` value is the only enabling mode. `public`, blank, missing, and all other values resolve to public-safe behavior; client request data cannot select the backend mode.

## 3. Implementation Architecture

`LOCT_RELEASE_MODE` is resolved in Python by `battle_api/release_mode.py` and in the frontend by `web-ui/lib/releaseMode.ts`. The backend evaluates it while building the ASGI app. `battle_api/app.py` includes the dedicated `battle_api/debug_routes.py` router only in Development. The ordinary battle/session routes remain in the main app and are not forked.

For the frontend, `web-ui/scripts/build-public-release.mjs` copies independent source files into ignored `web-ui/.public-release-source/` while filtering the two Engineering route directories, generated output, dependencies, and local `.env*` files. Vinext runs against that staged tree with Public mode. `release-artifact-policy.mjs` scans the built server/client output for excluded route entries/page modules and `DebugBattleExperience`, then writes a `public` marker. Only after verification is the generated artifact copied to `web-ui/dist`. `verify-public-release.mjs` is the `npm start` preflight and refuses missing, Development, or contaminated artifacts. An explicit Development build/serve path remains available.

Server page entry points pass mode-derived booleans to client components. `web-ui/app/stages/page.tsx` gates the Engineering link and hotspot query; `web-ui/app/game/page.tsx` passes the readout mode through the shared Battle experience, including Arena and Debug routes. `web-ui/vite.config.ts` defines the exact release-mode expression at build time to keep server/client rendering consistent. The browser does not calculate or authorize the mode.

## 4. Files Created or Modified

| Area | Files | Role |
| --- | --- | --- |
| Backend mode and route | `battle_api/release_mode.py`, `battle_api/debug_routes.py`, `battle_api/app.py` | Fail-closed mode resolution and conditional debug POST registration; no engine/adapter change. |
| Backend startup | `Makefile`, `docs/web-ui/PYTHON_ADAPTER_API.md` | Explicit local Development and Public backend startup/inspection. |
| Frontend mode, pages, presentation | `web-ui/lib/releaseMode.ts`, `web-ui/vite.config.ts`, `web-ui/app/{stages,game,debug}/page.tsx`, `web-ui/components/stages/StageSelectionScreen.tsx`, `web-ui/components/battle/{BattleExperience,ArenaRunExperience,DebugBattleExperience,BattleScreen}.tsx` | Server-supplied release mode and Development-only link, overlay, and viewport readout. |
| Frontend build/start | `web-ui/package.json`, `web-ui/.gitignore`, `web-ui/scripts/{build-public-release,release-artifact-policy,verify-public-release,prepare-development-build,mark-development-artifact}.mjs`, `web-ui/README.md` | Disposable pre-discovery route pruning, artifact guard, explicit commands, ignored staging. |
| Regression tests | `tests/test_release001_isolation.py`, `tests/test_ui023_arena.py`, `web-ui/tests/{release-001-frontend,release-artifact-policy,battle-presentation-config,ui-023-arena-debug}.test.tsx` | Two-mode route/API/presentation/artifact checks and explicit Development assumptions in older tests. |
| Architecture/contract/flow and task evidence | `docs/Technical/{Architecture,Networking}.md`, `docs/web-ui/{WEB_UI_ARCHITECTURE,BATTLE_DATA_CONTRACT_V1,Screen_Flow,Style_Guide}.md`, `docs/Codex/{Current_Task,Completed,Engineering_Test_Production_Isolation_Implementation}.md` | Stable release-boundary description, pre-code dispatch, visual/flow rules, and completion evidence. |

The completed audit file is preserved unchanged and remains untracked as supplied. No owner-controlled `UI_Review_Human.md` or player save data was intentionally edited. The exact final worktree inventory is checked at closeout.

## 5. Frontend Isolation Implementation

The Public build never deletes route files from the live checkout. Filtering happens while copying into a disposable, ignored staging tree, where `app/debug/` and `app/assets/` are absent before vinext inspects file routes. Shared battle and asset modules remain available for ordinary pages. The artifact policy rejects route entries/page paths or a `DebugBattleExperience` page-specific bundle; `npm start` refuses an unmarked, Development-marked, or contaminated artifact. `npm run build:development` and `npm run start:development` intentionally retain the Engineering routes.

Public UI presentation is separately gated at server entry points. The Stage Map does not render the Engineering link, even if a user supplies `?debugHotspots=1`; the same query activates three geometry labels in Development. The Battle viewport readout is opt-in from the server-provided mode and remains visible in Development. This defense-in-depth UI gating is not substituted for removal of the direct routes.

## 6. Backend Isolation Implementation

`battle_api/release_mode.py` treats only exact `LOCT_RELEASE_MODE=development` as Engineering enabled. `battle_api/app.py` conditionally includes `create_debug_router(registry)` at process import; Public, missing, and invalid modes never register `POST /api/v1/debug/battles`. FastAPI therefore returns 404 for a manually constructed request and omits the path from OpenAPI. Changing a query, header, or body field cannot register a route. Mode changes require a new server process.

In Development, the handler still accepts the established strict `CreateDebugBattleRequest` and calls the same `BattleRegistry.create` path with the selected seed/team/formation. It does not read/write the progression store. The public health, roster, normal battle, command, preview, stage, Arena, and save/progression routes were not moved or modified for this isolation.

## 7. Development and Production Commands

From repository root, local combined Development: `make dev`; backend only: `make backend`; same-Wi-Fi development: `make lan`. From `web-ui/`, `npm run dev` explicitly selects frontend Development on port 3001. For an explicit Development production-style frontend artifact, use `npm run build:development` then `npm run start:development`.

From `web-ui/`, Public frontend: `npm run build` then `npm start`. From repository root, Public backend: `make backend-public`. The latter listens on port 8001 and explicitly sets `LOCT_RELEASE_MODE=public`; it is a local startup command, not a GCE deployment recipe. A bare `uvicorn battle_api.app:app` without the mode is public-safe. To inspect the backend resolver, run `LOCT_RELEASE_MODE=development .venv/bin/python -m battle_api.release_mode` or substitute `public`. The frontend artifact marker is `web-ui/dist/.loct-release-mode`; `node web-ui/scripts/verify-public-release.mjs` checks Public artifact contents rather than trusting the marker alone.

## 8. Automated Test Results

Focused backend isolation: `tests/test_release001_isolation.py` — **4 passed** with one pre-existing Starlette/httpx deprecation warning. It uses a temporary progression database and covers Public 404/OpenAPI omission (including spoofed mode request data), missing/invalid fail-closed resolution, Development debug creation, and health.

Development Arena/debug regression: `LOCT_RELEASE_MODE=development .venv/bin/pytest -q tests/test_ui023_arena.py` — **12 passed**. Existing UI-023 tests were adjusted to express Development assumptions explicitly, without a process-global environment mutation.

Focused frontend mode/readout/debug tests: `npm test -- --run tests/battle-presentation-config.test.tsx tests/release-001-frontend.test.tsx tests/ui-023-arena-debug.test.tsx` — **33/33 passed** after updating directly affected UI-023 and readout expectations. Artifact-policy temporary-directory tests: `npm test -- --run tests/release-artifact-policy.test.ts tests/release-001-frontend.test.tsx` — **7/7 passed**, covering valid Public marker plus missing/Development markers and forbidden route/page-bundle content. `npm run typecheck` passed; `npm run lint` passed with zero errors and one unrelated existing unused `_signal` warning in `battle-transparency-preview.test.tsx:60`.

A broader Public-mode backend representative run reported **256 passed, 2 existing failures** in `test_ui027_gallery_metadata.py` (Priest Holy Concentration inventory expectations). The command was `LOCT_RELEASE_MODE=public .venv/bin/pytest -q` over `test_battle_api.py`, `test_battle_adapter.py`, `test_ui006_identity_and_logs.py`, `test_ui014_roster.py`, `test_ui018_formations.py`, `test_ui019_formations.py`, `test_ui020_progression.py`, `test_ui021_save_slots.py`, `test_ui027_gallery_metadata.py`, `test_ui028_skill_reference_metadata.py`, `test_ui033_battle_stats.py`, `test_ui062_formation_demonstration.py`, and `test_release001_isolation.py` (all under `tests/`). A broader frontend `npm test -- --run` across Startup, Stage Map, Team Builder, structured stages, formations, progression/save, Arena/Debug, Manual/Gallery, and Battle Screen reported **3 unrelated failures**: `ui-017-stage-and-structured-config.test.tsx` has an old `useSearchParams` mock, `ui-021-save-slots-and-previews.test.tsx` has a stale Paladin Altar geometry expectation, and `ui-028-hero-gallery-presentation.test.tsx` has a stale responsive CSS regex. The directly affected Engineering-link expectation was corrected and its focused suite passes. See Gameplay Regression Results for the limitation this places on a completely green broad suite.

## 9. Production Artifact Verification

`npm run build` completed and listed only normal frontend routes. The generated `web-ui/dist/.loct-release-mode` reads `public`. Artifact scanning found no `/debug` or `/assets` route entry/page module and no `DebugBattleExperience` page-specific client chunk in server/client output. This is an actual local Public build check, not evidence about any deployed host. The build script's verified scan is also a required precondition for `npm start`.

The independent reviewer also started the verified Public artifact locally with `npm start` and observed direct HTTP `/` **200**, `/stages?debugHotspots=1` **200** without Engineering link or hotspot SSR props, `/debug` **404**, and `/assets` **404**. The local socket required environment approval; this was an actual process/HTTP check, not a deployed-host test. The frontend specialist's later Public run found `/`, `/stages`, and `/game` **200** and the two excluded paths **404**. A Development-marked artifact was deliberately rejected by Public `npm start`; the final Public artifact was rebuilt afterward.

## 10. Gameplay Regression Results

The representative backend run covered battle API, adapter, progression/save, formations, Arena, Gallery metadata, and Hero Stats; 256 tests passed and the two Gallery inventory assertions above failed for unrelated existing Holy Concentration expectations. The focused Development Arena/debug suite passed 12/12. Frontend focused Stage/Engineering and artifact suites passed. The normal frontend Public build and typecheck passed. These checks give coverage for normal route preservation and 1v1/2v2/3v3 command/preview paths through existing suites, but they are not a claim of a full manual walkthrough of every screen.

Live Development server checks found `/debug` and `/assets` **200** and `/stages?debugHotspots=1` rendered the Engineering link and three hotspot labels after correcting release-mode compile-time substitution. Public direct-route/SSR checks are in Section 9. In an isolated ego-browser Public session at `http://127.0.0.1:3011` with a 1613×838 Chromium viewport, the Stage Map had no `/debug` link or `[data-testid=stage-hotspot-debug]` elements, no hydration error text was observed, client navigation from `/stages` to `/` worked, and direct `/debug` and `/assets` showed Not Found. With an isolated temporary backend database (`/private/tmp/release001-browser.sqlite3`) and Public API mode at `127.0.0.1:8011`, `/game?stage=warriors-barrack` launched a 2v2 battle shell; the viewport readout and its accessible label were absent and no browser alert was observed. Both processes and the isolated browser space were stopped, the temporary database was removed, and the final default-origin Public artifact was rebuilt. This is a representative live integration smoke, not a claim that all battles or progression outcomes were manually played. The automated suites cover Main Menu, Stage Map, Campaign/Team Builder, Gallery, Battle UI, 1v1/2v2/3v3 formations/commands/preview, Arena, and save/progression paths; the unrelated baseline failures above remain. Real player save files were not used.

## 11. Known Limitations and Outstanding Risks

The only build examined is the local vinext artifact generated for this task. GCE ingress, reverse proxy, TLS, deployed frontend files, environment variables, and live public reachability were not checked. Public-mode security depends on using the documented Public artifact and backend startup; the artifact guard prevents ordinary `npm start` from accidentally serving a Development build, but it is not a substitute for deployment controls or authentication.

Manual browser verification was desktop-only at 1613×838; tablet/mobile were not repeated because this task does not change responsive layout. The browser smoke did not manually finish a 1v1, 3v3, or Arena run or perform a full reward commit; relevant automated suites and their baseline failures are reported above.

The broader test suites are not completely green due the pre-existing Gallery inventory and stale frontend expectations listed above. A clean release gate should resolve those unrelated baselines separately. The Python battle registry remains process-local; public abuse/rate limiting and active-session resource policy are not part of Task A.

## 12. Pending Release Requirements

Public players must not be allowed to choose battle seeds; Task A deliberately preserves the existing optional-seed contract for Development testing. Player Name + Recovery Code/identity, authenticated save-slot ownership, shared-slot migration and backup, production ingress/TLS, API abuse controls, and the policy for generic free-form battles remain separate owner-approved work. This implementation must not be presented as solving those risks or as authorization to deploy.

## 13. Final Implementation Status

**Task A implementation complete; no deployment authorization or overall public-release readiness claimed.** The focused two-mode, artifact, runtime, browser, and representative gameplay gates passed. The independent reviewer approved the release boundary with no blocking implementation finding and separately confirmed Public direct HTTP behavior, artifact integrity, backend route isolation, and preservation of shared game code. Broader unrelated baseline test failures and the separate release blockers remain explicit in Sections 8, 11, and 12. No commit, push, branch, tag, or deployment was performed.

**Owner disposition, 2026-11-11:** The two Holy Concentration failures in
Section 8 are outdated test assumptions, not a restriction on which heroes may
have passives. Passives are never clickable battle commands. The current
implementation nevertheless makes Holy Concentration a Gallery-only passive
reference, not a separate Battle UI skill card; showing it there would require
a follow-up implementation decision. The `useSearchParams` mock and Paladin
Altar hotspot-coordinate failures are also stale test expectations. The
responsive Gallery CSS failure is a text-pattern mismatch: the one-column
rule exists, but the test expects it to be the first rule inside the media
query. These findings are **classified**, not yet cleared from the test suite;
the five failing assertions still require focused test maintenance (and a
visual hotspot check before accepting changed coordinates). The original
test counts above remain the results actually observed.

**UI-065 resolution, 2026-11-11:** The follow-up now shows Holy Concentration
as a non-clickable, presentation-only Battle card for Priest Discipline; it
still is not a runtime Skill, legal action, status, or new Redemption effect.
The two outdated backend inventory assertions were corrected to distinguish
the catalogue from runtime skills without restricting passives to named heroes.
The three stale frontend tests were corrected for the current navigation
provider, Paladin Altar source geometry, and order-independent 620px Gallery
grid rule. Focused backend Gallery tests now pass **7/7**, and the focused
frontend Stage/Gallery/presentation suite passes **59/59**; the UI specialist's
four-file Battle/Stage/Gallery suite passes **72/72**. Typecheck, targeted lint,
and diff check pass. The Paladin Altar location was checked against current
`stage-config.ts` source, not manually verified in a browser. This note does
not revise RELEASE-001's historical 256-pass/2-fail and three-frontend-failure
execution results above; it records their subsequent resolution.
