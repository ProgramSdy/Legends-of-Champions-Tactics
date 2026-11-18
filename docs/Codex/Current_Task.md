# Current Task

**Task:** RELEASE-002 — Batch 3 Implementation: Public Frontend Integration, Deployment Readiness & Final Release Validation

**Status:** Completed for local implementation and validation only; independently reviewed. Public deployment/launch remains unauthorized.

**Owner authorization date:** 2026-11-17

## Objective and authority

Complete Phase 8 (Public frontend integration) and Phase 9 (deployment-readiness tooling, configuration templates, backup/restore, isolated load tests and final release validation) of `docs/Codex/Task_B_Implementation_Plan.md`, with checkpoints A–C. Batch 1 and Batch 2 are complete and independently reviewed: see their implementation reports and `docs/Codex/Completed.md`. The prior `Current_Task.md` explicitly marked Batch 2 complete, so this replaces a finished task, not active work.

The owner's **full attached brief is authoritative**: `/Users/daoyu/.codex/attachments/53ea379a-56cf-4b18-9cf7-d39fb2e77f92/Pasted text.txt`. Read it in full before implementation. This task is a handoff summary, not a reduction of its requirements. **Deployment readiness is not deployment permission:** do not deploy to GCE, expose Public access, change live infrastructure/DNS/TLS/firewall, migrate a real database, launch the game, commit or push without separate owner authorization. Keep `BATTLE_API_ENABLE_PUBLIC_BATTLES` default-off; `=1` is allowed only in isolated local integration/test environments.

## Preparation and baseline

Read `docs/README.md`, `docs/onboarding/ONBOARDING_SUMMARY.md`, `docs/Codex/{Project_Rules,Agent_Roles,Current_Task,Task_B_Implementation_Plan,Task_B_Batch_1_Implementation_Report,Task_B_Batch_2_Implementation_Report}.md`; `docs/Technical/{Architecture,Networking,Player_Data_and_Save_System}.md`; and `docs/web-ui/{WEB_UI_ARCHITECTURE,Style_Guide,Screen_Flow,BATTLE_DATA_CONTRACT_V1,PYTHON_ADAPTER_API}.md`. Read selected role definitions. Inspect the **actual** Batch 1/2 API contracts and current `web-ui/lib/battle/liveProvider.ts`, Startup, Stage/Arena/Battle screens, session/save callers, `battle_api/{app,public_identity,progression}.py`, release configuration, tests, build scripts and deployment files. Do not assume the original plan's endpoint shapes are final. Record a relevant isolated baseline suite before significant edits; preserve unrelated dirty and owner-controlled files.

## Phase 8 — Public frontend integration

### Player entry, recovery and five slots

Implement a minimal dark-fantasy onboarding flow: Create New Player; validate 3–20 ASCII `[A-Za-z0-9_]` name (preserve case; duplicates allowed); use server-issued Player ID; display the securely generated `XXXX-XXXX-XXXX-XXXX` Recovery Code **only** at issue; Copy; explicit saved-code confirmation via the backend before normal Public access; then show that player's five slots. Explain that losing both session and code prevents self-service recovery. Support code-only Recover Existing Player and authenticated Forgot Recovery Code replacement, which invalidates the old code. No email/password, rename, ordinary Regenerate or unnecessary account feature. Never persist code/token in browser durable storage, URL, analytics or logs.

Centralize a Public session-aware frontend/provider and credentialed, same-origin transport using Batch 1's `Secure; HttpOnly; SameSite=Lax` host-only cookie and actual CSRF/Origin contract. Never read the HttpOnly token or invent client auth. Handle new/existing session, explicit protected refresh (ordinary GET/polling must not renew), sliding expiry, logout, recovery/revocation, CSRF rejection, network failure and multiple tabs. On revocation, stop protected requests, clear sensitive in-memory/player-specific views and return to onboarding/recovery; stale UI must confer no authority. Preserve Development anonymous behavior.

After authentication plus server acknowledgment, keep exactly five player-owned save slots, independent active selection and existing create/load/overwrite behavior. Use authenticated Public APIs; never treat client Player/Profile ID as authority. Keep roster, Stage, Arena, progression and Hero screens functionally and visually stable; avoid broad redesign or cross-player data leakage.

### Battle flow, Resign, warnings and receipts

Connect Public Stage/Arena launch, protected state/command/preview, server terminal/receipt, session errors, capacity/expiry/abandonment and existing 1v1/2v2/3v3 presentation to the **implemented** Batch 2 contract. Do not call Development generic creation or send caller-selected seeds in Public. Preserve combat mechanics and Development completion flow. Do not turn on the default-off Public battle feature gate outside isolated local tests.

Keep the existing Resign Yes/No modal. No sends nothing; Yes sends authenticated server Resign and waits for authoritative acknowledgment before leaving. On failure/timeout, do not claim success; keep a recoverable retry or state-refresh path. Handle Victory, expiration and revocation races without duplicate side effects.

Use Batch 2 `serverNow` and `expiresAt` for non-intrusive, one-time warnings at five and one minute per relevant deadline, correcting clock skew and updating only on authoritative deadline changes. Rerender/polling/UI/preview/playback must not extend server inactivity or duplicate warnings. Do not show a false timeout against server-active state. Server terminal/expired state wins.

Confirmed Victory already has a durable settlement/receipt. Display authoritative outcome and original receipt only; never invent reward or send a second reward-granting operation. Recover the same receipt after a lost response. Terminal-pending failures must not appear as confirmed Victory; offer only backend-permitted recovery. Never retry a timed-out command with a **different** command ID automatically.

**Checkpoint A — Frontend:** Automated and isolated browser checks cover new player/name/code/copy/acknowledgment/recovery/replacement, session refresh/expiry/multi-tab/old-device revocation, five slots, reload/direct navigation, no browser-stored secrets or cross-player data, Public Stage/Arena/state/command/preview, Resign success/failure/retry, 5/1 warnings with skew/rerender, durable receipt recovery, Development parity and desktop/narrow layouts. Resolve failures before Phase 9 closeout.

## Phase 9 — deployment readiness and local release validation

### Reproducible artifacts and configuration

Keep one repository with Development/Public configurations. Verify Public frontend build excludes `/debug`, `/assets` and page-specific engineering bundles; Public API omits Engineering Debug and generic battle creation; no secrets/Development data leak into artifacts; normal assets and player routes remain. Development engineering workflows must continue. Inventory the Production source/runtime/generated/config files needed to deploy. Hiding UI alone is not a security control.

Prepare **templates/runbooks only** for GCE e2-micro (~1 GB), one FastAPI worker, Nginx, same-origin HTTPS, persistent SQLite, process supervision/restart, frontend build, secure cookie, exact Origin/CSRF, trusted proxy/client IP, environment variables, logs, safe upgrade and rollback. Mark required domain/IP/certificate/topology values as unknown; do not provision or modify cloud infrastructure. Do not add Redis/PostgreSQL/Kubernetes/extra workers without an approved need.

Review recovery HMAC/verifier key, session/CSRF material, DB path, proxy/Origin, release mode and battle gate. No secret in source, DB, frontend bundle, docs or logs; Public missing critical settings fail closed, with no Development fallback. Document restrictive file permissions and protected backup/recovery of the verifier key.

### SQLite backup, schema and rollback

Implement locally testable **consistent SQLite online backup** tooling: daily backups, pre-release backup, seven daily retained, separately designated release backups, integrity check and isolated restore validation; plan protected off-VM GCS transfer and credentials. Do not raw-copy a live WAL database. If GCS credentials/access are unavailable, mark remote transfer **NOT VERIFIED**, not successful. Never overwrite live DB during a restore drill. Document schedule, retention, commands, integrity/schema checks, key recovery and rollback limitations.

Document explicit clean Public v5 initialization, durable path and `public_battle_schema_revision=2` verification. Prepare the backup-first, offline upgrade path from legitimate Batch 1-shaped databases if needed, and test it **only on disposable copies**. Runtime must not silently rewrite schema. Do not import Development v4 saves or migrate a real DB.

### Load and release gates

Run isolated representative tests for 20 simultaneous 3v3 battles and 21st rejection, one-per-player, concurrent commands, session recovery, expiry/Resign capacity release, concurrent Victory settlement, SQLite contention/busy, disk-full/write-failure and restart reconciliation. Measure CPU, peak RSS, transaction/lock behavior, latency, failure counts and recovered capacity. Local results **do not prove e2-micro capacity**; if measured risk warrants, recommend a lower limit. Do not claim GCE/TLS/proxy/GCS behavior verified without actual evidence.

**Checkpoint B — Security/artifact/operations:** Public and Development builds/mode routes, default-off battle gate, cookie/CSRF/Origin/trusted proxy/rate limit, DB role/schema fail-closed, no secrets, backup and isolated restore, startup missing-config failure all pass locally; deployment-only checks remain visibly pending.

**Checkpoint C — Stress and final regression:** Batch 1, Batch 2, RELEASE-001, Development backend, frontend integration, typecheck/lint/build, Stage/Arena/combat, fault/concurrency and capacity checks pass or have explicit truthful blockers. Record exact commands, counts, warnings, failures and limitations. Do not hide or weaken tests, use live player data, or present local VM-independent measurements as GCE evidence.

## Documentation deliverables and stop

Update directly affected Technical, web-ui/API, deployment and operational docs. Create `docs/Codex/Task_B_Batch_3_Implementation_Report.md` with Phase 8/9 implementation and changed files; onboarding/code/session/CSRF/five-slot/battle/Resign/warning/receipt behavior; build exclusions; GCE/Nginx/secret readiness; backup/restore and schema-upgrade evidence; stress measurements; exact tests; reviewer findings; and remaining deployment-only validation. For every significant claim label **IMPLEMENTED**, **LOCALLY VERIFIED**, **REQUIRES DEPLOYMENT VERIFICATION**, **BLOCKED**, or **NOT IMPLEMENTED**.

Also create `docs/Codex/RELEASE_002_Public_Launch_Readiness_Checklist.md` covering source/build, identity/session, data isolation, battle ownership/capacity, Resign/timeout, settlement, RNG/diagnostics, SQLite backup/restore, HTTPS/Nginx/proxy, GCE resources, rollback/recovery and **owner launch authorization**. Each item needs status, evidence, remaining action and whether it blocks Public launch; clearly mark actual GCE-only checks.

Core must stop for a product-level decision, material gameplay change, unsatisfied security gate, live infrastructure requirement or real DB migration. At completion, report concise results and both file paths, then **wait for explicit owner deployment/Public-launch authorization**. Do not deploy, enable Public users, change live resources, migrate real saves, push, commit/tag/release or declare the game publicly launched.

## Pre-code coordination gate — Core, 2026-11-17

This is a high-risk frontend/authentication plus operations release candidate,
not a Public launch. All five roles are selected with distinct work: PM owns
Checkpoint A→B→C dependencies and stop gates; UI owns Phase 8 frontend and
responsive behavior; engine owns bounded backend contract/backup/schema and
deployment-readiness tooling; test automator owns independent integration,
fault/load and restore coverage; reviewer owns independent security and
readiness review. PM, UI and engine were dispatched in the first wave; test
automator and reviewer are scheduled for later waves under the four-agent
concurrency limit. Core owns cross-boundary integration, documentation and
final validation. No role is omitted. The critical sequence is actual Batch
1/2 contract inventory and isolated baseline → Phase 8 implementation and
Checkpoint A → safe local Phase 9 tooling/validation and Checkpoint B → stress,
full regression and independent review at Checkpoint C. Key risks: secret
exposure in browser state, wrong CSRF/cookie same-origin assumptions,
duplicate battle command on timeout, unacknowledged Resign, incomplete or
unsafe SQLite backup, and claiming local measurements prove GCE readiness.

Before significant edits, the isolated Public baseline
`.venv/bin/python -m pytest -q tests/test_release002_batch2.py
tests/test_release002_batch1_security.py tests/test_release001_isolation.py`
passed **78/78** with one existing Starlette/httpx deprecation warning;
targeted frontend release tests passed **7/7**. Existing dirty work, owner
files, live databases and deployment configuration remain preserved.

## Current closeout checkpoint — 2026-11-18

Batch 3 source, operations templates, the 21-section implementation report,
and the Public Launch Readiness Checklist are in the shared worktree. Focused
Public backend checks pass 96/96; separate explicit-Development backend
regression passes 572/572; relevant frontend groups pass 103/103; typecheck,
lint (one pre-existing warning), Public/Development builds, Python compile,
and diff check pass. Disposable local HTTPS browser checks exercised
onboarding, code acknowledgment/replacement/recovery, five slots, protected
reload/logout, a Public 2v2 preview/command, Resign, and Secure cookie
attributes. Narrow 390px DOM widths fit; screenshot capture timed out twice.
Test-only stale-expectation repairs resolved the five older presentation
files. The **full** frontend suite now passes 58 files/553 tests; one
intervening run had a single intermittent UI-033 timing failure, then its
isolated 6-test file and the next full 553-test run passed. The independent
reviewer rechecked source, the full frontend suite, report/checklist and diff,
then approved local Batch 3 closeout with no remaining P0/P1 code or
documentation-claim issue. This Completed status does not approve deployment
or Public launch.
GCE/Nginx/TLS/GCS/real-legacy-DB and owner-launch gates remain
explicitly open regardless of local results. The local test browser, API,
frontend and disposable DB/certificate were closed/removed. No commit, push,
deployment or real database change occurred.

## Agent assignments

**Assessment:** High-risk, cross-system release integration. Select and actually dispatch `project-manager` for A→B→C dependencies/scope and release gates; `ui-developer` for onboarding, session-aware transport, save/battle/Resign/warnings and responsive accessibility; `game-engine-developer` for API/settlement compatibility, safe offline schema/backup tooling and backend security boundaries (no combat-rule edits); `test-automator` for integration, multi-tab/device, backup/restore, stress/fault and mode regressions; and independent `reviewer` for auth/secret exposure, deployment/backup safety and settlement/race review. Core integrates, records actual dispatch/contributions, and may run roles in waves. Keep cross-chat traffic to one completion report or a genuine owner-decision blocker.
