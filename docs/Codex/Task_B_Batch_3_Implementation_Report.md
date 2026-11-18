# RELEASE-002 Batch 3 — Local Implementation and Validation Report

**Date:** 2026-11-18

**Scope:** Phase 8 (Public frontend) and Phase 9 (deployment-readiness tooling and local release checks)

**Status:** Local implementation and validation complete; deployment/Public launch **not authorized**
**Authority:** `Current_Task.md` and the owner’s full RELEASE-002 Batch 3 brief. This report does not grant deployment, live migration, commit, push, or Public enablement.

Status terms in this report are literal: **IMPLEMENTED** means source exists; **LOCALLY VERIFIED** means an identified local test/check passed; **REQUIRES DEPLOYMENT VERIFICATION** means no GCE/domain/Nginx/TLS proof exists; **BLOCKED** means the next required step needs new authority or an unavailable fixture; **NOT IMPLEMENTED** means deliberately outside this batch.

## 1. Executive summary

**IMPLEMENTED:** Public player onboarding, session-aware frontend transport, five-slot selection, Stage/Arena battle integration, server-acknowledged Resign, inactivity warnings, and durable receipt recovery now consume the Batch 1/2 backend authority. Local configuration, backup/restore, schema inspection, narrow offline upgrade, and deployment templates have been added. The Public battle route gate remains default-off. Development battle paths remain separate.

**LOCALLY VERIFIED:** Focused Public backend and frontend tests, separate Development regression, local HTTPS browser onboarding, Public build exclusion, SQLite backup/restore, and a disposable 20-battle/capacity/concurrent-reservation harness are described below. These checks are not GCE capacity or live-launch proof.

**REQUIRES DEPLOYMENT VERIFICATION:** Actual HTTPS certificate/domain, Nginx forwarding, systemd sandbox/restart, GCE e2-micro resource behavior, remote GCS backup/restore, and operational recovery remain untested on a deployment host. **BLOCKED:** any actual legacy Public database upgrade requires an authorized disposable copy of its real schema. **NOT IMPLEMENTED:** RAM battle resume after process restart, replay of an uncommitted terminal result after simultaneous storage failure and process crash, and any new account mechanism.

## 2. Phase 8 implementation results

**IMPLEMENTED:** `PublicSessionProvider` is the in-memory session boundary. Public requests use same-origin URLs, browser credentials, and the server-issued CSRF token; Development retains its existing local adapter transport. Startup supports creation, code-only recovery, one-time code acknowledgment, authenticated code replacement, and logout. Protected Stage and Game routes gate on the acknowledged session. Existing server-owned five-slot screens are reused. Public Stage/Arena launches use owner-bound routes and server-generated seeds, then consume protected state/commands/previews/receipts. Battle presentation remains the existing 1v1/2v2/3v3 system.

## 3. Phase 9 implementation results

**IMPLEMENTED:** `public_config.py` validates the intended Public environment, and Public identity routes fail closed without the independent rate-limit key rather than relying only on service supervision or health. `public_db_ops.py` provides read-only schema/integrity inspection, SQLite online backups, seven-daily retention, separately retained release backups, exclusive 0600 backup/manifest creation, isolated no-overwrite restore validation, and a narrowly guarded offline Public-v5 marker upgrade. `deploy/public/` contains non-deployed environment, Nginx, systemd, timer, GCS-transfer and operational templates. No live file or infrastructure was changed.

## 4. Changed files and modules

Batch 3 source modules: `web-ui/lib/publicApi.ts`, `web-ui/components/session/PublicSessionProvider.tsx`, `web-ui/app/layout.tsx`, `web-ui/components/startup/StartupScreen.tsx`, `web-ui/app/stages/page.tsx`, `web-ui/app/game/page.tsx`, `web-ui/components/battle/{BattleExperience,ArenaRunExperience,BattleScreen}.tsx`, `web-ui/lib/battle/liveProvider.ts`, `web-ui/lib/manual/formationDemonstration.ts`, `web-ui/vite.config.ts`, `web-ui/README.md`, `battle_api/{app,public_config,public_db_ops}.py`, and `deploy/public/*`. Batch 3 test modules: `tests/test_release002_batch3_{operations,load}.py`, targeted Public-fixture updates in `tests/test_release002_batch{1_security,2}.py` and `tests/test_release001_isolation.py`, plus `web-ui/tests/release-002-*`. Final regression repair adjusted test-only expectations/harness in `web-ui/tests/{ui-008-opening,stage-two-automation,battle-transparency-002,battle-backgrounds,paladin-protection-figure}.test.tsx`. Existing Batch 1/2 dirty changes in other files were preserved; this is not a claim that every dirty file belongs to Batch 3.

Batch 3 documentation updates: `docs/Technical/{Architecture,Networking,Player_Data_and_Save_System}.md`, `docs/web-ui/{WEB_UI_ARCHITECTURE,Style_Guide,Screen_Flow,BATTLE_DATA_CONTRACT_V1,PYTHON_ADAPTER_API}.md`, `deploy/public/README.md`, this report, the launch-readiness checklist, `Current_Task.md`, and the completion log. The GDD was not changed because Batch 3 adds no combat formula, hero ability, reward rule or gameplay decision; existing Stage/Arena authority is consumed, not redefined. The API/contract docs describe frontend consumption and do not claim a new `1.0` schema.

## 5. Player onboarding and Recovery Code flow

**IMPLEMENTED:** New names are checked against the owner-approved 3–20 ASCII letter/digit/underscore rule without treating a name as identity. The backend issues Player ID and `XXXX-XXXX-XXXX-XXXX` code. The code is displayed only at issuance or authenticated replacement; the player must explicitly confirm safe storage, and the backend records acknowledgment before normal Public access. The UI explains that loss of both code and session prevents self-service recovery. Code-only recovery revokes the previous device session; replacement invalidates the old code and requires new acknowledgment. No password, email, ordinary regenerate, rename, or browser-durable Recovery Code storage was introduced.

## 6. Session and CSRF frontend integration

**IMPLEMENTED:** HttpOnly session cookie authority stays entirely server-side. Public `fetch` uses `credentials: include`, same-origin URLs, and an in-memory CSRF token on unsafe methods. Initial/current-session GET is read-only; an explicit protected refresh POST is initiated near expiry when visible, not by ordinary GET/polling. Authentication failure clears in-memory player views and broadcasts invalidation to tabs; a CSRF 403 revalidates read-only and does not replay an unsafe mutation. Network and server failures remain distinct. The backend requires exact Origin/CSRF and validates trusted proxy/client IP.

## 7. Five-slot ownership integration

**IMPLEMENTED:** After recovery-code acknowledgment, the existing five-slot UI consumes authenticated Public save-slot APIs. Slot create/load/confirmed overwrite and active-slot selection remain backend-owned. Browser Player ID, Profile ID and URL state do not authorize writes. Development’s anonymous five-slot behavior remains available only in explicit Development mode.

## 8. Public battle integration

**IMPLEMENTED:** Public Stage/Arena launch, battle state, command, preview, Resign and completion use the Batch 2 owner-bound routes. Generic/Debug creation is never a Public fallback, and the browser does not send a caller-selected Public seed. The opt-in `BATTLE_API_ENABLE_PUBLIC_BATTLES=1` was used only in a disposable local integration process; the default setting remains off. Combat engine rules, formation legality, and presentation are unchanged.

## 9. Resign and timeout UX

**IMPLEMENTED:** The existing Yes/No confirmation remains: No does not submit; Yes sends authenticated server Resign and waits for acknowledgment before leaving. A failure retains retry/reconciliation rather than claiming success. Five-minute and one-minute warnings use `serverNow`/`expiresAt` clock-skew correction and one-time threshold tracking per authoritative deadline. A same-deadline preview update does not erase a warning; changed deadline or terminal state resets it. Reads, previews and UI playback do not extend the server deadline.

## 10. Victory receipt and failure handling

**IMPLEMENTED:** Terminal Public Victory is displayed only from the server-confirmed settlement and original receipt. An uncertain command retry reuses the exact command ID; it does not create a second operation. Receipt recovery reads the durable result instead of granting again. Terminal-pending or server failure is not presented as confirmed Victory. A process restart cannot resume an unfinished RAM battle; only already durable receipts survive.

## 11. Public build contents and exclusions

**LOCALLY VERIFIED:** The Public frontend artifact passes its marker/exclusion check and omits Engineering `/debug` and `/assets` page bundles, the temporary origin sentinel, and the Development `localhost:8001` adapter string in a full `web-ui/dist` scan. The player-facing Manual formation catalogue now uses the same Public same-origin API boundary; Public transport selects an empty/same-origin base URL. Explicit Development build and routes remain available. This artifact check is not a production deployment.

## 12. GCE, Nginx and HTTPS readiness

**IMPLEMENTED as templates only:** `deploy/public/` defines one FastAPI worker, loopback API/web services, Nginx HTTPS ingress, a single overwritten `X-Forwarded-For`, Uvicorn `--no-proxy-headers`, strict Public environment validation, systemd supervision, and persistent database/backup paths. Domain, certificate, firewall, VM, actual process sandbox and Nginx behavior are **REQUIRES DEPLOYMENT VERIFICATION**. The web unit’s runtime-writable state beyond its configured log path must be tested under the real unit before launch.

## 13. Secrets and environment configuration

**IMPLEMENTED:** Public startup/health and identity route construction require an explicit Public DB, exact HTTPS Origin, strong versioned identity HMAC key, distinct strong rate-limit HMAC key, and trusted proxy IP list. Environment templates contain placeholders, not live secrets. The Recovery Code verifier key and version must be retained in protected off-DB recovery material; a database backup alone cannot validate old codes after key loss. File/secret permissions and non-logging guidance are documented in `deploy/public/README.md`. Actual secret-manager provisioning is **REQUIRES DEPLOYMENT VERIFICATION**.

## 14. SQLite backup and restore evidence

**LOCALLY VERIFIED:** Disposable tests exercise SQLite’s online backup API during WAL/concurrent writes, SHA/integrity/schema checks, seven-daily retention without pruning release backups, exclusive/no-overwrite destinations, isolated restore, and rollback on injected upgrade failure. The operational timer and remote GCS script are templates. Actual timer execution, encrypted off-VM transfer, GCS download, and restore from remote storage are **REQUIRES DEPLOYMENT VERIFICATION**.

## 15. Schema initialization and upgrade procedure

**IMPLEMENTED:** Clean Public DB initialization is explicit via `python -m battle_api.init_public_db` at an absent external path, followed by `public_db_ops inspect` requiring role `public`, schema v5, battle-schema revision 2, and integrity. Runtime never silently upgrades. A confirmation-gated offline upgrade accepts only an exact modeled Batch 1 Public-v5 foundation signature, makes a release backup first, and atomically inserts revision 2. **BLOCKED for a real legacy DB:** the tests have a modeled old shape, not an authorized genuine deployed legacy fixture; any real DB must be inspected/backed up/rehearsed separately before migration permission.

## 16. Resource and stress-test measurements

**LOCALLY VERIFIED only:** Disposable local tests create 20 real 3v3 adapter sessions, submit one command per session, reserve 20 distinct-player Public SQLite leases, reject a 21st, and release leases on Resign. A separate 20-thread test exercises concurrent `BEGIN IMMEDIATE` Public reservations without observed busy failures. In the final local `-s` run, adapter launches took 174.46 ms total and commands 14.65 ms total; Public lease p95 was 0.60 ms, command p95 1.29 ms, cleanup 10.43 ms, process CPU 231.00 ms, and peak RSS 117,325,824 raw bytes as reported by the macOS harness. The contention test had maximum reservation latency 74.32 ms and zero busy failures. These are one-host sample values, not latency guarantees. The harness does **not** establish 20-session performance on a GCE e2-micro or test real Nginx/TLS/client network latency, disk pressure, or long-running memory behavior.

## 17. Exact automated and browser validation

**LOCALLY VERIFIED commands:**

- `.venv/bin/python -m pytest -q tests/test_release002_batch3_operations.py tests/test_release002_batch3_load.py tests/test_release002_batch2.py tests/test_release002_batch1_security.py tests/test_release001_isolation.py` — **96 passed**, one pre-existing Starlette/httpx deprecation warning. The final local load sample came from `.venv/bin/python -m pytest -q -s tests/test_release002_batch3_load.py` — **3 passed** with the metrics in §16.
- `LOCT_RELEASE_MODE=development .venv/bin/python -m pytest -q tests --ignore=tests/test_release001_isolation.py --ignore=tests/test_release002_batch1_security.py --ignore=tests/test_release002_batch2.py --ignore=tests/test_release002_batch3_operations.py --ignore=tests/test_release002_batch3_load.py` — **572 passed**, the same warning. A single combined-process run with Public test modules produced 11 stale global-`registry` failures after `battle_api.app` reload; it is not counted as a clean broad pass and the suites were rerun separately by release mode.
- `npm test -- tests/release-001-frontend.test.tsx tests/release-002-frontend-public-api.test.ts tests/release-002-frontend-session.test.tsx tests/release-002-phase8-ui.test.tsx tests/release-002-battle-receipt.test.ts tests/ui-021-save-slots.test.tsx tests/ui-021-save-slots-and-previews.test.tsx tests/ui-023-arena-debug.test.tsx` — **45 passed**. A second relevant group (`battle-screen`, `ui-017-stage-and-structured-config`, `ui-021-stage-previews`, `release-artifact-policy`, `ui-012-stage-selection`) — **58 passed**. The groups total **103/103** focused/relevant frontend checks.
- `npm run typecheck`, `npm run lint`, `npm run build`, `npm run build:development`, and a final `npm run build` all passed. Lint had zero errors and one existing unused `_signal` warning in `tests/battle-transparency-preview.test.tsx:60`. The final Public artifact verifier passed; full `dist` scans found no `localhost:8001` or `sentinel.invalid` literal and no Engineering Debug/Assets page bundles. `.venv/bin/python -m py_compile battle_api/app.py battle_api/public_config.py battle_api/public_db_ops.py` passed.
- Full frontend `npm test` passed **58 files / 553 tests** after test-only repair of stale accessible-control/timing assumptions in `ui-008-opening`, `stage-two-automation`, `battle-transparency-002`, `battle-backgrounds`, and `paladin-protection-figure`. No production behavior was changed for those tests. One subsequent full-suite run had a single intermittent timing failure in `ui-033-battle-stats-integration`; that file passed **6/6** when rerun alone, and the next full run passed **553/553**. This intermittent test timing is a residual harness risk, not hidden as an uninterrupted pass. Final `git diff --check` passed after all edits.

**Local browser evidence:** A disposable Public DB, test-only keys, loopback API, self-signed `https://localhost:3101` frontend, and local API proxy (not Nginx) were used; the opt-in battle gate was enabled in that isolated process only. The browser created a player, displayed a correctly shaped one-time code without logging it, required the saved-code checkbox, acknowledged it, displayed five slots, created slot 1, directly reloaded `/stages`, and showed empty local/session storage. It entered a Public 2v2 Warrior stage, loaded an authoritative Fireball target preview, selected a target and executed one server-driven command. Resign No left battle active; Yes returned after server acknowledgment and an SQLite read showed zero active leases. Authenticated code replacement required new acknowledgment; after logout, code-only recovery restored the same player; a second logout and direct `/stages` visit showed the protected-session gate. Cookie metadata (values not read) showed host-only `__Host-loct_session` with Secure/HttpOnly/SameSite=Lax and a Secure non-HttpOnly CSRF cookie. At 390px, Stage Map and Team Builder DOM widths did not exceed the viewport. Ego-browser screenshot capture timed out twice, so pixel-level narrow visual validation is **not claimed**. This local self-signed topology is not deployed TLS/Nginx proof.

## 18. Independent reviewer findings and resolutions

**Actual role dispatch and ownership:** Project manager `/root/batch3_pm`
mapped A→B→C sequencing, stop gates and operational risks (no source edit).
UI developer `/root/batch3_ui` owned Public transport/provider, entry,
protected routes, battle UX and focused frontend checks. Game-engine
developer `/root/batch3_engine` owned Public configuration, narrowly scoped
auth fail-closed integration, offline DB tools and deployment templates.
Test automator `/root/batch3_tests` owned independent operations/load tests,
frontend boundary tests and final legacy test-harness repair (tests only).
Reviewer `/root/batch3_reviewer` performed independent read-only security,
artifact, race and readiness review. Core owned cross-boundary integration,
isolated HTTPS browser checks, final command reruns and documentation. All
five required roles were actually dispatched; no role is credited for work it
did not perform.

The independent reviewer found and the assigned owners corrected: (1) Public identity route could accept a missing/weak/non-independent rate key even though health failed; (2) player-facing Manual formation rules still used the Development localhost URL; (3) a preview authority update could clear a currently visible inactivity warning; and (4) initial load coverage lacked concurrent SQLite reservations. The reviewer rechecked those source fixes, the full 553-test frontend suite, Public artifact exclusion, this report/checklist and `git diff --check`, then **approved Batch 3 for local implementation/validation closeout only**, with no remaining P0/P1 code or documentation-claim issue. This approval is explicitly not permission to deploy, enable Public battles, migrate a real DB or launch. The UI-033 timing observation, missing pixel-level screenshot, and all deployment/owner gates remain recorded limitations.

## 19. Outstanding deployment-only validation

**REQUIRES DEPLOYMENT VERIFICATION:** owner-approved domain/certificate, Nginx exact Origin/CSRF/Secure-cookie/trusted-peer behavior, systemd sandbox and restart, persistent disk/permissions/backup timer, GCS upload-download-restore, secret recovery, GCE e2-micro CPU/RSS/latency under 20 active 3v3 sessions, capacity/lock/disk-pressure behavior, rollback drill, alerting/log rotation, and firewall/DNS. None was performed or implied by local HTTPS testing.

## 20. Known limitations and residual risks

**NOT IMPLEMENTED:** RAM battle resume after restart or automatic recovery of a terminal result not yet durably settled when both storage and process fail. Public client cannot fabricate a receipt or grant reward. The exact offline legacy upgrade path is intentionally narrow; unknown real schema fails closed. Local self-signed HTTPS testing, if successful, verifies browser behavior only under a disposable proxy and does not establish deployed TLS/Nginx. Existing frontend lint may retain one unrelated `_signal` warning. Local 20-session values are not VM capacity proof.

## 21. Final RELEASE-002 readiness assessment

**IMPLEMENTED/LOCALLY VERIFIED and independently approved for local closeout:** Batch 3 source, focused Public/frontend checks, separate Development backend, full frontend regression (with the intermittent timing caveat above), builds, and the isolated browser path above. **BLOCKED for Public launch:** no separate owner deployment authorization; no actual GCE/TLS/Nginx/GCS/resource/rollback validation; no real legacy DB migration rehearsal if one is needed. `BATTLE_API_ENABLE_PUBLIC_BATTLES` remains default-off. Stop at local implementation and await explicit owner direction before any deployment, real DB change, enablement, commit, push, release or launch.
