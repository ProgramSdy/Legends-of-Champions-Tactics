# RELEASE-002 Batch 1 Implementation Report

**Date:** 2026-11-16

**Scope:** Approved Phases 1–3 only: Public player identity, authentication, and player-owned saves. This report is not Public launch approval.

## Outcome and sequence

1. **Checkpoint A — database foundation:** Added an explicitly initialized, clean Public SQLite schema v5 with a `database_role=public` marker. Public runtime requires `BATTLE_API_PUBLIC_DB` as an absolute path outside the repository and refuses a missing, wrong-role, incomplete, or incompatible database. `python -m battle_api.init_public_db /absolute/path/to/new.sqlite3` is the one-time initializer and refuses an existing file. Development retains its separate anonymous schema-v4 database and unchanged save workflow. Foreign keys, critical ownership keys, the one-active-session partial unique index, integrity checks, and transactional rollback are validated.
2. **Checkpoint B — identity and session:** Added server-generated Player ID, case-preserving non-unique Player Name, one-time 80-bit Recovery Code, keyed/domain-separated verifier, saved-code acknowledgment, code-only recovery, authenticated replacement, one active device session, revocation/logout, 30-day sliding expiry, bounded credential rotation with a 60-second same-device previous-token grace, and persistent per-IP recovery-abuse blocking. Public unsafe requests require exact configured Origin and session-bound CSRF; GET validation is read-only and explicit protected refresh renews the session.
3. **Checkpoint C — player-owned data:** Public players each receive slots 1–5 and an independent active selection. Save, progression, Stage listing, and Arena state/run operations resolve the authenticated player's owned profile. Protected reads and writes recheck session generation, expiry, revocation, and saved-code acknowledgment inside SQLite transactions; writes use `BEGIN IMMEDIATE`. Existing Stage, Arena, and reward behavior in Development remains unchanged.

## Changed implementation files

| File | Batch 1 role |
| --- | --- |
| `battle_api/progression.py` | Public schema/validation, separate player slots/active selection, ownership and transaction-level session checks while preserving Development v4. |
| `battle_api/public_identity.py` | Credential generation/verifiers, sessions, code-only recovery, rotation/refresh, CSRF verification, and persistent IP rate limit. |
| `battle_api/init_public_db.py` | Explicit one-time clean Public database initializer; never overwrites existing data. |
| `battle_api/models.py` | Typed identity/session/recovery request and response models. |
| `battle_api/app.py` | Public configuration, identity routes/cookies/Origin/CSRF, owned progression routes, and registration-level Public battle gate. |
| `tests/test_release002_batch1_security.py` | Disposable-database schema, identity, session, ownership, and route isolation regressions. |
| `tests/test_release001_isolation.py` | Public health fixture now supplies an explicitly initialized disposable Public database. |

The directly affected technical/API documents are `docs/Technical/Architecture.md`, `docs/Technical/Networking.md`, `docs/Technical/Player_Data_and_Save_System.md`, `docs/web-ui/PYTHON_ADAPTER_API.md`, and `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`. `docs/Codex/Current_Task.md` records dispatch and completion. No UI implementation was authorized for Batch 1, so the Style Guide and screen-flow documents need no Batch 1 behavior change.

## Public API and security contract

`POST /api/v1/players`, `POST /api/v1/sessions/recover`, `GET /api/v1/sessions/current`, `POST /api/v1/sessions/refresh`, `POST /api/v1/recovery-code/acknowledge`, `POST /api/v1/recovery-code/forgot`, and `POST /api/v1/sessions/logout` form the backend identity surface. Enrollment and authenticated replacement are the only Recovery Code disclosure points; responses with session or code material use `Cache-Control: no-store`. The session cookie is host-only `Secure; HttpOnly; SameSite=Lax`; the CSRF value is not the authentication secret. An unconfirmed player cannot use ordinary Public save/progression routes. Recovery uses a canonical client IP accepted from a forwarded header only when the immediate peer is an explicitly trusted proxy; failures are keyed by an HMAC digest, with the tenth failed attempt inside 15 minutes starting a 15-minute block.

Public save/progression/Stage/Arena operations require the validated player session and derive Player ID server-side. No client-supplied Player/Profile ID grants authority. Public static hero/manual catalogues remain read-only. Public routing and OpenAPI omit **all** battle creation, state, command, preview, and completion paths, including generic `POST /api/v1/battles`. Development keeps generic, Stage/Arena, and Debug battle operations. The Public lease/diagnostic/settlement tables are schema-only foundations, not active battle lifecycle features.

## Validation evidence

- Public/RELEASE-001 isolated security suite: `.venv/bin/python -m pytest -q tests/test_release002_batch1_security.py tests/test_release001_isolation.py` — **25 passed**, one pre-existing Starlette/httpx deprecation warning. This includes a same-player concurrent slot-create race (one success/one `slotOccupied`) and cross-session Arena mutation denial.
- Existing Development progression/slot/Arena/mode/attempt suites: `LOCT_RELEASE_MODE=development .venv/bin/python -m pytest -q tests/test_ui020_progression.py tests/test_ui021_save_slots.py tests/test_ui023_arena.py tests/test_mode001_integration.py tests/test_rng001_attempts.py` — **44 passed**, same warning.
- Broader Development backend suite, excluding the two Public-mode files run separately above: `LOCT_RELEASE_MODE=development .venv/bin/python -m pytest -q tests --ignore=tests/test_release002_batch1_security.py --ignore=tests/test_release001_isolation.py` — **572 passed**, same warning.
- `python -m py_compile` of the changed backend modules and Public initializer: passed.
- Frontend compatibility: `npm run typecheck` passed; `npm run lint` passed with one pre-existing unused `_signal` warning; targeted RELEASE-001 frontend/artifact tests **7 passed**; `npm run build:development` passed. No frontend source was changed for Batch 1.
- `git diff --check`: passed.
- New migration/security SQLite tests used disposable fixture paths and test-only keys. **No real Development or Public save database was intentionally targeted, migrated, overwritten, or deleted.** No deployment, commit, push, tag, or release was performed.

Tests run in separate Public/default and explicit Development processes because the safe default mode is Public and route registration happens at module import. A mixed-mode legacy test command without an explicit mode is not a valid Development regression check.

## Independent roles and review

`project-manager` mapped A→B→C dependencies and gates; `game-engine-developer` owned the backend schema/routes/store integration; `test-automator` owned the isolated security and compatibility regressions; `ui-developer` audited frontend caller compatibility read-only (Batch 3 UI intentionally deferred); `reviewer` independently checked the auth/ownership/schema/Public-route boundary. The reviewer found two issues during implementation—GET session mutation and incomplete schema-shape validation—which were fixed and rechecked. Final independent result: **approved; no remaining Batch 1 blocking findings**.

## Deferred scope and prerequisites

Batch 2 must implement Public battle ownership, one-per-player/global capacity leases, inactivity/Resign, seed policy, outcome/settlement durability and diagnostics before any Public battle endpoint opens. Batch 3 must add same-origin session-aware frontend onboarding and transport. Deployment still needs verified HTTPS/private proxy/forwarded-IP topology, protected secrets, consistent backup/off-VM retention and restore drill, and resource/load validation. The Public database initializer must run only against an approved new durable path. A green Batch 1 suite and this review do **not** authorize Public player testing or launch.
