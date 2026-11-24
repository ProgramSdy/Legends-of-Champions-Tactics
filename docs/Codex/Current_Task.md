# Current Task

**Active assignment (2026-11-24): Stage 5.1 — Bug Fix Release & Rollback Validation.** The Owner has authorized Core to proceed with **Batches A–D** of `docs/Codex/Stage_5_1_Bug_Fix_Release_and_Rollback_Validation.md`: fix the three confirmed bugs, verify them, and prepare a reviewed release candidate. **Batch E — production deployment and actual rollback validation — still requires separate Owner approval after candidate review.** Do not deploy, change the live GCE server, or treat release-candidate preparation as Public Alpha launch authorization. BUG-002 must cover every `battlePresentationConfigFor` viewport mode—monitor, laptop-large, laptop-medium, pad, pad-mini, phone and portrait—with actual browser visual evidence, not just desktop/mobile testing. Core must resolve or escalate any product-level BUG-003 Tactics Level ambiguity before changing gameplay policy. Preserve existing player data and the installed capacity setting of 200. Stage 4 remains Owner-accepted/closed; final Alpha launch approval remains pending.

## Historical status — Stage 4 closure and earlier assignments

**Current status (2026-11-23): Stage 4 — Performance & Load Testing is OWNER-ACCEPTED / CLOSED.** Stages 1 and 2 are complete for their defined Alpha scope; Stage 3 is Owner-accepted. The final Stage 4.3 production run had 30/30 selected players start and settle a battle, and a read-only server observation found 30 simultaneous active leases. The installed battle-capacity setting is now 200, but only 30 concurrent leases were demonstrated. The authoritative measurements, prior 10/20-player runs, unsuccessful earlier 30-player participation attempt, and limits are in `docs/Codex/Stage_4_2_1_Implementation_Report.md`. **No further Stage 4 production load testing is currently authorized.**

**Next gate: Final Public Alpha Launch Readiness Review — not yet approved or completed.** Review remaining launch requirements and accepted residual risks, then seek an explicit Owner go/no-go decision. Stage 4 closure does not authorize launch, a new implementation stage, 50/100-player tests, or production changes. See `docs/Codex/RELEASE_002_Public_Launch_Readiness_Checklist.md`.

## Historical Stage 4.2.1 assignment and local closeout

**Original assignment (2026-11-22): Stage 4.2.1 — Concurrent Battle Load Tester.** Core was initially authorized to implement a guarded Python load-testing tool and verify it only against a local or isolated environment. The original brief is `docs/Codex/Stage_4_2_1_Concurrent_Battle_Load_Tester.md`. At that point, no production load test, production write, live GCE change, or use of real player accounts was authorized. Later production trials and the capacity-only change had separate Owner approvals; see the implementation report. Tool support for 10/30/50/100 players did not itself authorize a live escalation.

**Local implementation completed 2026-11-22; production trial not authorized.** The guarded CLI, 16 focused new tests, disposable two-player HTTPS Public API run, data-isolation/retention analysis and independent local-only review are recorded in `docs/Codex/Stage_4_2_1_Implementation_Report.md`. The successful second local sample was 2/2 complete 3v3 friendly victories with 143/143 requests succeeding; this does not establish deployed GCE or Nginx capacity. The proposed first production command is **only a proposal** in that report and still requires separate Owner approval, confirmation of installed rate limits, and acceptance of permanent dedicated test-player records. No further Stage 4 load level was started.

**Reusable-pool follow-up completed locally 2026-11-22.** At the Owner's direct request, the tester now has explicit protected create/reuse/reconcile modes and incremental pool-size targets. The dated follow-up in `Stage_4_2_1_Implementation_Report.md` records the additional focused tests, disposable HTTPS creation/recovery/reuse, privacy controls and interrupted-run procedure. The current test file has 24 focused cases; no production run, production data change or higher-concurrency load level occurred. The initial Stage 4.2.1 validation above remains its historical evidence.

## Stage 4.2.1 pre-code coordination gate — Core, 2026-11-22

This is a security- and data-sensitive external test tool, not a game or UI
feature. Selected: project-manager (safe sequence, data/production gates),
Python/API implementation specialist (guarded CLI and actual Public contract),
test-automator (independent deterministic guard/metrics/local integration tests),
and reviewer (final independent security and correctness review). The first
three were dispatched before implementation; reviewer is reserved for the
post-validation wave. UI-developer is omitted because no frontend work is
authorized. Core owns documentation, integration and final handoff.

Sequence: verify Public authentication, slot, Stage launch, command and receipt
contracts plus installed-rate-limit unknowns; implement default no-write and
strict non-production targeting; exercise two independent disposable local
players; run focused tests; obtain independent review; record permanent-data
implications and a proposed, **unexecuted**, two-player production command.
Main risks are accidentally hitting the known public host (including redirects),
retaining secrets in output/CSV, unsafe account creation on a durable database,
and mistaking a battle-rule rejection or expired session for performance loss.

## Historical completed assignment — RELEASE-002 Batch 3

**Task:** RELEASE-002 — Batch 3 Implementation: Public Frontend Integration, Deployment Readiness & Final Release Validation

**Status:** Historical Batch 3 implementation completed and independently reviewed. Public HTTPS and core-gameplay milestones passed on 2026-11-19. Stages 1–2 passed their defined checks, and Stage 3 Security & Release Management was Owner-accepted for Public Alpha with residual risks on 2026-11-20. Final Alpha launch readiness remains pending.

**Historical planning snapshot (2026-11-20, superseded):** This earlier documentation update assigned no new Core task. At that date Stages 1–2 were complete for their defined checks, Stage 3 was Owner-accepted, and Stage 4 had not yet started. The Owner reported Nginx hardening, tested rate limiting, HTTPS/TLS with a passed Certbot renewal dry-run, and reviewed SSH/firewall exposure. The selected Single-Release Strategy retained one deployed release; actual rollback was deferred to the next release. Public SSH port 22 with key authentication and local-only seven-backup SQLite protection were accepted Alpha risks. The then-planned Stage 4 sequence was 2, 5, 10 and 20 concurrent players; the actual later production runs and closure are recorded at the top of this file. Do not infer final Alpha launch approval or a tested rollback from Stage 3 or Stage 4. The historical Batch 3 prohibitions below describe its original 2026-11-18 scope, not later separately authorized deployment, battle activation or operations work.

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
