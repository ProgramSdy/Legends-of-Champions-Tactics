# RELEASE-002 Batch 2 Implementation Report

**Date:** 2026-11-17 (Australia/Sydney)

**Scope:** Approved Phases 4–7 only. Public battle work is isolated backend/test implementation, not Public player launch approval.

## Gate sequence and role ownership

The required pre-code gate is recorded in `Current_Task.md`. This is a high-security-risk, cross-system change, so all five configured roles were selected. The `project-manager` mapped A→B→C→D dependencies and lock/acknowledgment risks; the `game-engine-developer` owns backend lifecycle, settlement and RNG; the `test-automator` owns isolated security/concurrency/fault coverage; the `ui-developer` performed a read-only client-contract audit with no Batch 3 UI implementation; and an independent `reviewer` checks the integrated security and settlement boundary. Core owns integration, documentation and final validation. No role was intentionally omitted.

The isolated baseline before Batch 2 edits was 25 Public Batch 1/RELEASE-001 tests passing and 44 relevant Development progression/Arena/attempt tests passing, each with one existing Starlette/httpx deprecation warning.

## Files and authority boundary

| File | Batch 2 role |
| --- | --- |
| `battle_api/progression.py` | Public battle-schema revision marker, SQLite lease/diagnostic/settlement authority, active/terminal transitions, Stage/Arena transaction-scoped Victory helpers, original receipt read. |
| `battle_api/adapter.py` | Fixed server battle-ID construction and removable RAM sessions; existing combat resolution remains authoritative. |
| `battle_api/attempts.py` | Owner/session-bound attempt lookup/bind/remove without holding a registry-global lock over session construction. |
| `battle_api/app.py` | Default-off Public route gate, per-player lifecycle coordination, authenticated owner-aware Stage/Arena launch and shared routes, Resign, terminal settlement before confirmed response, Public seed policy. |
| `battle_api/models.py` | Additive typed preview timing/lifecycle fields; combat snapshot/event shapes remain unchanged. |
| `tests/test_release002_batch2.py` | Disposable Public SQLite, fake-clock, concurrency, fault, route/auth, settlement, seed and release-mode regressions. |

Public Stage/Arena creation obtains a confirmed Player session, an owned active
slot/profile and server-authored stage/run context. It pre-generates the battle
ID and 256-bit seed. Under a per-player lock, one short `BEGIN IMMEDIATE`
transaction expires eligible stale leases, checks one battle per Player ID,
counts provisional and active global leases (initial cap 20), and inserts a
two-minute provisional reservation and diagnostic. RAM construction uses that
same ID outside SQLite; activation extends the server deadline to 30 minutes.
Construction/activation/binding faults remove the RAM session/attempt and
release the provisional reservation. A process restart reconciles RAM-
dependent unfinished leases; settled receipts/diagnostics remain durable.

Lock order is per-player lifecycle lock → battle/session lock → short SQLite
transaction. The engine's own RNG/session lock remains its existing internal
authority. No long combat resolution runs inside a SQLite transaction.
Protected Public state, command, preview, Stage/Arena completion receipt and
Resign routes authenticate and owner-check; a known foreign battle ID grants
no access. Launch attempts are bound to Player ID/session generation, profile,
route and ordered configuration, and replay cannot bypass lifecycle checks.

## Lifecycle, settlement and RNG

The Public lifecycle distinguishes provisional, active, resolving, terminal-
pending, settled, abandoned and expired states. Exact UTC server deadlines are
checked synchronously on protected operations. Only a newly accepted command
after full engine and automatic-AI resolution refreshes inactivity; GET,
preview, rejected/stale or duplicate command, AI processing alone and
animation do not. A resolving marker protects a valid in-flight action from
another player's lazy expiry cleanup. Resign is server-owned and idempotent;
before confirmed Victory it abandons without a reward and frees capacity.
It cannot undo an already committed result.

At terminal resolution, the API uses the engine's authoritative outcome, not
client input. One SQLite transaction verifies owner, immutable launch binding
and live lease; applies the existing Learner/Tactics Stage or Arena effect
for a friendly Victory; stores original result/receipt and diagnostic outcome;
and releases the lease. Defeat/Draw settle without a Victory reward. A later
completion request reads the original receipt rather than granting again.
Injected pre-commit failure rolls back reward, receipt and lease release; no
confirmed Victory is returned, and the server-authored terminal-pending
outcome remains retryable. The current authenticated owner can retry it even
after logout/recovery replaced the original session; the old session remains
revoked, and the persisted outcome and immutable launch context are used rather
than new client claims. A process crash before durable confirmation is not a
confirmed Victory; restart reconciliation expires that unfinished battle, and
full combat replay would require a battle journal outside this batch.

Public Stage requests containing `seed`—including explicit `null`—are
rejected. Public Stage/Arena combat uses a fresh secure 256-bit effective seed
stored as canonical 64-character hex in server-only diagnostics; it is never
returned to clients and is distinct from the persisted Arena schedule/node
seed. Development generic, Stage and Debug deterministic seeds remain.
Diagnostics retain battle/Player/launch context, build version, seed, UTC
times, lifecycle, outcome and receipt reference indefinitely for Pre-Alpha;
they exclude credentials, CSRF secrets and full replay.

## Route/release gate

Default Public mode remains closed to **all** battle routes. Exact server
configuration `BATTLE_API_ENABLE_PUBLIC_BATTLES=1` allows owned Stage/Arena
and shared battle routes only in isolated Batch 2 test processes. Generic
`POST /api/v1/battles` and Engineering Debug are absent from Public routing and
OpenAPI even with the opt-in. Development retains generic/Stage/Debug routes.
Public player onboarding, same-origin transport, UI Resign/warnings and any
deployment are later gates, not delivered here.

The Battle 2 lease/diagnostic tables have explicit
`public_battle_schema_revision=2` in a newly initialized Public v5 database.
A legitimate Batch 1-shaped v5 DB fails closed with an offline-upgrade
requirement; runtime never silently rewrites it. An owner-approved offline
migration on a verified backup is required before a later Public launch if
such a database contains data. No real DB was migrated here.

## Validation and independent review

Checkpoint A–D tests include cross-owner/session denial, concurrent one-player
and 20/21-player capacity, launch rollback, fake-clock expiry/Resign/command
ordering, Stage/Arena atomic reward and original-receipt retries, faulted
terminal-pending recovery through the HTTP route, 256-bit Public seeds,
development parity, route/OpenAPI isolation, and schema-revision fail-closed
with byte-level no-mutation verification. Final focused command:
`.venv/bin/python -m pytest -q tests/test_release002_batch2.py
tests/test_release002_batch1_security.py tests/test_release001_isolation.py`:
**78 passed**, one existing Starlette/httpx deprecation warning. The Batch 2
file alone: **53 passed**. Broader explicit-Development command:
`LOCT_RELEASE_MODE=development .venv/bin/python -m pytest -q tests
--ignore=tests/test_release002_batch2.py
--ignore=tests/test_release002_batch1_security.py
--ignore=tests/test_release001_isolation.py`: **572 passed**, same warning.
Frontend `npm run typecheck`, `npm run lint` (zero errors, one pre-existing
`_signal` warning), `npm run build:development`, `npm run build`, and seven
release-artifact frontend tests passed. The Public build excluded `/debug` and
`/assets`; the local artifact was not deployed. Changed Python modules
compiled, and `git diff --check` passed. The independent reviewer reproduced
the 78-test focused result and approved the final code, security boundary,
documentation, and recovery regression with no remaining blocker. Initial
review findings around revoked/resolving capacity, Resign/command ordering,
terminal-pending transitions, invalidation, expiry rollback and settled
receipt behavior were corrected; the final pending-after-recovery finding was
closed with current-owner persisted-outcome retry and HTTP fault coverage.
These local checks are not a deployed HTTPS/proxy or e2-micro load test.

Architecture, Networking, Player Data/Save System, Python Adapter API and
Battle Data Contract were updated for the implemented authority and additive
contract. Screen Flow, Style Guide and GDD need no Batch 2 edit: there is no
new player-facing UI, visual rule or combat formula; Batch 3 owns the eventual
Public client flow. No owner-controlled UI review file was touched.

## Release boundary and deferred work

Development schema v4 and combat rules must remain unchanged. Public uses disposable, explicitly initialized schema-v5 test databases only; no real save database was intentionally migrated, overwritten or used in testing. No deployment, Public player access, Batch 3 onboarding/frontend Resign/warnings, backup automation, commit or push is authorized by this batch. Browser/runtime HTTPS/proxy and resource/load evidence remain later release gates.
