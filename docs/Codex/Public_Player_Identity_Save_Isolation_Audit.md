# RELEASE-002 / Task B — Public Player Identity, Save Isolation & Random Seed Strategy Audit

**Date:** 2026-11-11 (Australia/Sydney)

**Method:** Read-only inspection of the current working tree; no live database, player record, API mutation, or deployed host was examined.
**Status:** Audit and proposal only. No implementation or public-deployment approval.

**Role record:** Core synthesized this report; `game-engine-developer` traced backend/data/RNG, `ui-developer` traced frontend/session/release integration, and `reviewer` independently checked security severity and report evidence with no blocking finding. A separate project manager was unnecessary for this bounded audit, and no test-automator was dispatched because no implementation or new test harness was authorized.

## 1. Executive Summary

**Verified:** RELEASE-001 separates Development engineering routes/artifacts from Public builds, but the normal API is still an unauthenticated, single-user local design. It has five *global* save slots, one global active slot, process-local battles, and public routes that accept some caller-chosen battle seeds. A Public artifact can therefore be release-mode clean while still unsafe for multi-player Internet use (`battle_api/app.py:61-89,193-265,500-606,621-766`; `battle_api/progression.py:278-290`; `battle_api/release_mode.py:17-32`). CORS is a browser-origin filter, not authorization.

**Reusable:** Stable local profile and battle identifiers, server-owned stage/Arena definitions, the existing transaction/receipt pattern, scoped engine RNG-state capture, and fail-closed release mode. **Must change:** identity/session authority, per-player save ownership, lifecycle authorization, revocation/cleanup, Public seed policy, and production database placement/backup. **Deferrable:** full online accounts, PvP, live battle resume, full replay, and database replacement. Keep one repository, existing engine/mechanics, and five player-facing slots where practical.

The current source declares SQLite **schema version 4**, not 3 (`battle_api/progression.py:19,376-405,511-541`). Earlier version-3 descriptions are historical and must not drive migration design. A staged migration on a backed-up copy is required; do not automatically attach existing local profiles to an arbitrary new online player.

## 2. Current Architecture Overview

The browser fetches the Python FastAPI service directly through `LiveBattleProvider`; the shared request helper sends JSON without a credential policy (`web-ui/lib/battle/liveProvider.ts:59,84-114`). FastAPI constructs one `ProgressionStore`, one `BattleRegistry`, and one `BattleAttemptRegistry` at import (`battle_api/app.py:80-89`). The store defaults to `data/player_progression.sqlite3` inside the repository unless `BATTLE_API_PROGRESSION_DB` overrides it. The registries are process-local dictionaries (`battle_api/adapter.py:4099-4149`; `battle_api/attempts.py:34-80`).

Current flow: Startup lists/creates/loads a global slot → stage/Arena or free-form launch reads the globally active profile → `BattleRegistry.create` makes a RAM session → `/battles/{id}` and its command/preview routes use only the supplied battle ID → friendly victory can commit to the launch profile only while that same profile remains globally active (`battle_api/app.py:193-265,350-470,500-766`). This active-profile check prevents some wrong-slot writes but is not player authentication.

The release-mode boundary is **reusable**: only explicit `LOCT_RELEASE_MODE=development` registers debug creation (`battle_api/release_mode.py:17-32`; `battle_api/app.py:88-89`). It does not change ordinary route authorization or seed validation. A bare backend process defaults to Public behavior; `make backend-public` and frontend Public build/start are local commands, not evidence of live deployment (`Makefile:24-25`; `web-ui/package.json:12-19`).

## 3. Identity and Authentication Findings

**Missing (verified):** No Player Name, recovery-code verifier, Player ID account, device session, auth cookie/token dependency, logout, recovery, revocation, or session expiry appears in the current API models/routes/store (`battle_api/app.py:166-766`; `battle_api/models.py:890-988`; `battle_api/progression.py:273-360`). A local `profile_id` like `profile.local.slot.<n>.<uuid>` identifies a slot's progression record, not an authenticated person (`battle_api/progression.py:718-739`). The slot listing returns those IDs to any caller (`battle_api/progression.py:639-669`). Names must not serve as credentials or authorization keys.

**Must change:** Introduce server-generated unique Player IDs and a Player Name + Recovery Code enrollment/recovery flow. Names need not be globally unique under this task's approved requirement; the older online-pre-alpha paragraph suggesting unique names in `docs/Technical/Player_Data_and_Save_System.md` is a design-document conflict, not current code. Make recovery code cryptographically random, disclose it only at enrollment/regeneration, store a protected verifier rather than plaintext, use uniform/non-enumerating recovery errors plus rate limiting, and never log it. Issue a random opaque session secret in a `Secure`, `HttpOnly`, appropriately `SameSite` cookie; store only a protected verifier/session reference server-side. Successful recovery must revoke the previous session atomically so at most one device session is valid. Backend validation, expiry, revocation and logout must gate protected routes. Exact code entropy/format, TTL, rate limits, cookie topology and regeneration policy require owner/security design approval, not invented constants in this audit.

Current CORS has `allow_credentials=False`, only JSON content-type in allowed headers and configurable explicit origins (`battle_api/app.py:61-78`). **Must change** credentialed cross-origin handling if frontend/API remain on separate origins, or prefer same-origin reverse proxy; validate origin/CSRF, TLS, cookie domain and `SameSite` in the actual deployment. Simply adding `credentials: 'include'` on the browser without corresponding server policy would fail; merely enabling CORS would not authorize direct HTTP callers.

## 4. Save Slot and Progression Findings

**Reusable (verified):** SQLite stores profiles, unlocked heroes, stage progress, mode completions, rewards, Arena runs/nodes and idempotent completion receipts. Slot initialization, load, Arena mutation, and victory use `BEGIN IMMEDIATE`; v1→v2→v3→v4 migrations are explicit (`battle_api/progression.py:269-374,376-541,671-810,1175-1260,1346-1413,1467-1614`). A five-slot UI need not be discarded.

**Must change:** `save_slots.slot_id` is the primary key for values 1–5, and `active_slot` has one singleton row (`battle_api/progression.py:278-290,366-370`). `_active_profile_id` selects through that singleton; `list_save_slots`, create/load/overwrite and progression reads/writes contain no Player ID predicate (`battle_api/progression.py:614-669,671-810`; `battle_api/app.py:193-283`). One caller can switch or overwrite the slot another is using. Profile-scoped tables prevent some accidental cross-profile *database* updates, but caller ownership is absent.

| Current owner/key | Target owner/key | Disposition |
| --- | --- | --- |
| `profiles.profile_id` (local progression identity) | `players.player_id` plus slot/profile row | Preserve profile IDs internally where migration can prove ownership; do not equate them with account identity. |
| `save_slots.slot_id` 1–5 globally | `(player_id, slot_id)` 1–5 per player | Retain five-slot presentation and isolate create/load/overwrite. |
| `active_slot(singleton_id=1)` | Player-scoped active slot or authenticated session selection | Never use a global selector for Public calls. |
| Unlocks, stage/mode progress, rewards, receipts keyed by profile | Profile tied by FK/ownership to one Player ID and slot | Enforce player predicate throughout service methods/transactions. |
| `arena_runs.profile_id`, nodes by run | Player-owned profile/run and server-authored nodes | Preserve current run logic but authorize every read/launch/abandon/commit. |
| RAM battle/attempt by opaque ID | RAM battle/attempt with immutable Player ID, save-slot/profile, and session generation | ID is a lookup key, not permission. |

**Migration/unknown:** Existing local slots may contain genuine owner progress, shared testing data, or both; the code cannot infer a rightful online owner. Snapshot and validate the current DB *without reading private rows into reports*, then use an explicit owner-approved one-time claim/import or leave it as Development-only data. Protect against duplicate claim; preserve rollback copy and migration ledger. Do not silently reset or export a live save.

## 5. Battle Session and Reward Ownership Findings

**Verified:** Stage/Arena launches bind `progression_profile_id`, stage/mode or run/node context into the session (`battle_api/app.py:350-415,538-619`; `battle_api/adapter.py:459-479`). `BattleAttemptRegistry` keys retries by attempt ID plus profile/fingerprint, but has no player/session identity or cleanup (`battle_api/attempts.py:34-80`). Free-form `/api/v1/battles` checks that its team is unlocked for the global active profile but stores no launch owner on the session (`battle_api/app.py:500-526`). Battle state, commands and preview look up an ID without checking a caller (`battle_api/app.py:621-700`). Any party possessing an ID can operate that session; opaque IDs are not authorization.

**Reusable but insufficient:** Completion verifies the authoritative ended friendly-victory snapshot under the session lock, then uses transactionally stored receipts; Arena also enforces current-node order (`battle_api/app.py:427-468,712-766`; `battle_api/progression.py:1346-1413,1467-1614`). The `expected_profile_id` vs *global* active profile prevents redirect to a different active slot, but does not establish requester ownership and can reject a legitimate completion after an unrelated caller switches the global slot. Revoked sessions cannot be distinguished.

**Must change:** Bind the authenticated Player ID, immutable launch slot/profile and session generation to every Public battle and attempt. Enforce ownership for creation, state, command, preview, completion and reward settlement. The same transaction that writes receipt/progression must verify owner/profile binding and currently valid session generation; a revoked session or overwritten slot cannot finish a protected write. Preserve existing idempotent receipts, and define lock order between session and SQLite operations to avoid deadlocks. On save overwrite, invalidate battles tied to that exact old profile. Do not use a newly selected slot to redirect an old battle's reward.

No live-battle resume is approved. RAM registries currently have no TTL or eviction (`battle_api/adapter.py:4099-4149`; `battle_api/attempts.py:34-80`). **Must change:** bound lifetime/capacity, abandon/cleanup semantics, and retry scope. A browser-close event is not reliably delivered, so use best-effort unload notification plus server TTL/heartbeat or equivalent bounded expiry; never promise immediate close detection. A disconnected/recovered device may not continue commands or completion. Single-worker process assumption remains until registry sharing is designed.

Critical races to test: recovery revocation versus in-flight command/completion; old session versus slot overwrite; duplicate victory commit; active-slot change versus old battle; two simultaneous launches using one attempt ID; Arena run abandon/replacement versus old node completion. Authorization before a transaction alone is insufficient if revocation can commit between check and reward write.

## 6. Random Seed and RNG Findings

**Verified:** Generic battle and structured-stage models accept optional client `seed` (`battle_api/models.py:346-376,860-868`); the generic route passes it through, and stage launch uses it in preference to `secrets.randbits(256)` (`battle_api/app.py:500-526,577-619`). Arena combat already draws server entropy (`battle_api/app.py:365-405`). Arena schedule creation uses a server `secrets.randbits(63)` by default, stores schedule/node seeds, and shuffles a fixed 2/6/4 battle-size pool with `random.Random(schedule_seed)` (`battle_api/progression.py:1137-1171,1223-1255`). The store method also has an internal `schedule_seed` testing parameter, not an Arena request field. Development debug creation accepts its own seed behind the release-mode route boundary (`battle_api/debug_routes.py:13-45`).

The persisted Arena node `battleSeed` is legacy schedule data, **not** the actual live retry seed: each Arena battle launch deliberately draws a new `_fresh_battle_seed()` (`battle_api/progression.py:1024-1083,1240-1252`; `battle_api/app.py:365-405`). Diagnostic design must not label that stored node value as the combat seed or silently switch retries to it.

The adapter saves/restores module-global Python RNG state around seeded session construction and action processing, with per-session `rng_state` and locks (`battle_api/adapter.py:972-1098,1368-1379`). This supports deterministic seeded tests within the current single-process architecture, but it is not a cryptographic stream, a durable replay log, or proof of independent cross-process execution. Unseeded adapter creation calls `secrets.randbits(256)`, while the `BattleSession.seed` field can remain `None` when no seed was passed (`battle_api/adapter.py:459-479,972-979,1042-1043`); diagnostics should record the *effective* generated seed server-side if needed without exposing it to Public responses. Normal battle envelopes do not include a `seed` key (`battle_api/adapter.py:1280-1287`).

**Must change:** In Public, reject—not silently ignore—client seed fields on all normal creation paths, generate a server seed, and retain deterministic explicit-seed access only in Development/internal tests. Avoid a frontend-only restriction; direct callers must receive typed rejection. Decide the Public status of the generic free-form battle route separately. Do not echo server seeds in normal Public responses. Keep a minimal server-only diagnostic record: Battle ID, Player ID, launch slot/profile, effective seed, build/version, start time, final outcome/time if available, plus route/mode/stage or Arena node and hero/formation definition IDs needed to interpret it. Exclude recovery codes, session cookies and other credentials. Recommend configurable **30-day** diagnostic retention for the small pre-alpha cohort: enough for delayed defect reports while bounding sensitive metadata and disk use; owner should approve or alter this policy. This is not full replay.

## 7. Frontend Integration Findings

**Verified:** Startup currently lists/creates/loads the five backend slots and has no enrollment/recovery or credential persistence UI (`web-ui/components/startup/StartupScreen.tsx`; `web-ui/lib/battle/liveProvider.ts:84-114`). Main Menu/Stage Map, structured Team Builder, Arena Run, and Battle experiences consume the selected progression and process-local provider; the ordinary player stage launch omits the optional seed but the API still accepts it (`web-ui/components/battle/BattleExperience.tsx:49-58,337-363`; `docs/web-ui/WEB_UI_ARCHITECTURE.md:369-400`). The API base URL is a public frontend environment value, defaulting to `http://localhost:8001` (`web-ui/lib/battle/liveProvider.ts:59`). Current network error handling wraps disconnection and HTTP errors as `BattleProviderError`, not an authentication-invalidation workflow (`liveProvider.ts:84-114`).

The page entry points do not have a player/session guard: `/` renders Startup, `/stages` renders the map without a session request, and `/game` chooses a stage before the client loads progression (`web-ui/app/page.tsx:9-10`; `web-ui/app/stages/page.tsx:14-25`; `web-ui/app/game/page.tsx:15-24`; `web-ui/components/battle/BattleExperience.tsx:142-178`). Startup's accessible five-slot create/load/confirmed-overwrite interaction is **reusable** (`web-ui/components/startup/StartupScreen.tsx:115-179,220-326`). Its `profileId` checks are UI consistency keys, not credentials (`web-ui/components/battle/BattleExperience.tsx:153-165`; `ArenaRunExperience.tsx:122-135`). The dormant `web-ui/app/chatgpt-auth.ts` helper is not imported by current app code; it is a third-party auth template and must not be mistaken for the approved Player Name + Recovery Code system. Only sound preference, not credentials, currently uses browser local storage (`web-ui/components/audio/SoundPreferenceProvider.tsx:14,26-40`).

**Minimal integration, not implementation:** Add one shared credentialed transport/session layer to the existing provider; avoid per-screen auth copies. Startup should resolve session first, then show name entry + first-time Recovery Code disclosure/acknowledgment or recovery entry, then the current five-slot screen. On every protected fetch, handle expiry/revocation consistently and clear private in-memory battle/progression UI without treating a random 409 as logout. Recovery on a second device invalidates the first; old-device API errors should return to recovery/start rather than leaving stale commands enabled. Logout and code regeneration need explicit confirmation paths and server-backed invalidation. Preserve current visual/navigation patterns and five-slot semantics; no localStorage recovery code or JavaScript-readable bearer secret.

Frontend alone cannot guarantee browser-close abandonment or prevent forged slot IDs. The backend must own both; UI unload notification is only an optimization. Verify cookie transport across initial SSR/client navigation, refresh, direct links, and the configured frontend/API origins before Public release.

## 8. SQLite, Migration, Backup, and Deployment Findings

**Verified:** Store schema is v4; v1 default profile is transactionally placed into slot 1, v2 adds Arena, v3 adds mode completion history (`battle_api/progression.py:19,376-541`). Existing connections set foreign keys and a 5-second SQLite timeout, and critical mutations use `BEGIN IMMEDIATE` (`progression.py:235-260,269-374,671-810,1346-1413,1467-1614`). No explicit WAL, `busy_timeout` pragma, checkpoint or backup routine was found in this store. SQLite itself is not a blocker for one small, single-instance e2-micro pre-alpha; concurrent write contention, disk limits, backup integrity and restore time are the operational concerns.

**Must change operationally:** Set the Public DB path to durable persistent storage outside replaceable checkout/build artifacts (`battle_api/app.py:81-86`), strictly separate Development/Public DB paths and permissions, and fail startup if Public storage is unavailable rather than create a fresh empty DB in an accidental location. Plan migration on a copy with pre-migration backup, schema/integrity checks, rollback artifact, rehearsed restore, and an ownership-claim policy. Use online-consistent SQLite backup or a quiesced snapshot that includes WAL state if WAL is enabled; copying only the main `.sqlite3` while writes continue can be incomplete. Test out-of-disk, `SQLITE_BUSY`, and interrupted migration. Back up to storage outside the VM/release disk, encrypt/protect it, and rehearse a restore before collecting real player progress. Keep a single backend worker unless process-local battle ownership is redesigned.

The repository has RELEASE-001 build and route isolation but no inspected GCE ingress, TLS, firewall, persistent-disk, backup job, secret-store or deployed artifact evidence (`docs/Codex/Engineering_Test_Production_Isolation_Implementation.md:1-12,108-129`; `Makefile:24-25`). **Unknown:** actual host capacity, ingress exposure, file permissions, backup destination and restore objective; do not claim those controls exist. Public release packaging must exclude Development save data, temporary DB/WAL/SHM and secrets while retaining the persistent volume across redeploys.

Existing tests are a **reusable regression foundation**, not proof of public ownership: local slot overwrite/migration rollback and active-slot switch checks appear in `tests/test_ui021_save_slots.py:199-303`, stage reward rollback in `tests/test_ui020_progression.py:283-371`, and Arena rollback in `tests/test_ui023_arena.py:280-379`. No new tests or write-capable exploratory requests were run for this audit.

## 9. Security Risks and Severity

| Severity | Confirmed exposure or conditional risk | Evidence / impact |
| --- | --- | --- |
| **Critical public-release blocker** | No API authentication; global slots and active profile | If reachable publicly, any caller can enumerate/switch/overwrite shared progression and Arena state (`battle_api/app.py:193-335`; `progression.py:278-290`). |
| **Critical public-release blocker** | Battle ID acts as bearer access handle | Any holder can read/command/preview and potentially trigger completion without caller ownership (`battle_api/app.py:621-766`). Guessability is not assumed; disclosure/reuse is enough. |
| **High** | Caller-supplied Public seeds | Predictable/reproducible combat attempts on generic/stage routes (`models.py:346-376,860-868`; `app.py:500-619`); not a direct unlock bypass. |
| **High** | No revocation/expiry/cleanup for battle and attempt registries | Unbounded RAM and stale work; exploitability depends on reachable API and traffic (`adapter.py:4099-4149`; `attempts.py:34-80`). |
| **High** | Public default DB inside checkout, no verified backup | Redeploy/data-loss/corruption risk for real saves (`app.py:81-86`); actual host controls uninspected. |
| **Design-dependent** | Recovery guessing/enumeration and CSRF once identity is added | Not an existing recovery exploit because recovery does not yet exist; design controls are required before introducing it. |

This severity describes what would happen **if the current normal API were exposed to multiple public players**. No live penetration test or deployed-host inspection was performed.

## 10. Proposed Target Architecture

Keep the Python engine and adapter as combat authority, FastAPI as sole auth/progression boundary, one SQLite database for the Public single instance, and the existing React screen structure. Add a `Player` record, server-verifiable recovery credential, one active device session generation, player-scoped five slots, and immutable battle owner/launch-slot context. A request dependency resolves the authenticated Player/session; store methods take that context explicitly and enforce it in queries/transactions. Client-supplied IDs locate a resource only after an owner predicate. Public and Development remain in the same repository with distinct release mode, DB path, and seed policy. No new skill/formation/combat calculation is needed.

| Route group (current) | Current auth / ownership | Target Public policy |
| --- | --- | --- |
| `GET /health`, public hero catalogue, formation demonstration | None; static/read-only (`app.py:166-190`) | May remain public, rate-limit as appropriate. |
| Enrollment, recovery, session check/logout/regeneration (absent) | Missing | New narrowly scoped routes; abuse controls, secure cookie, one-session revocation. |
| `/save-slots` list/create/load/overwrite | Global singleton (`app.py:193-265`) | Auth required; Player ID + slot predicate, overwrite confirmation, active slot per player. |
| `/progression`, `/stages`, `/arena` read and run/create/abandon | Global active profile (`app.py:268-335,478-490`) | Auth required; resolve only caller-owned profile/run. |
| Generic `/battles` create | Global unlock gate, optional seed (`app.py:492-526`) | Owner decision on Public availability; if retained, auth, owner binding, server seed. |
| Stage/Arena battle create | Global active profile, stage/run guards (`app.py:350-415,529-619`) | Auth + launch slot binding, server seed, owner-scoped attempt key. |
| `/battles/{id}` state, command, preview | ID-only (`app.py:621-700`) | Auth + battle owner and current valid session check; stale/expired rejected. |
| Stage/Arena completion | Snapshot + current global profile (`app.py:418-470,703-766`) | Auth + battle owner/launch slot + live session generation in the receipt transaction. |
| `/debug/battles` | Development only (`app.py:88-89`) | Remain absent in Public; Development isolation retained. |

## 11. Minimal-Invasive Implementation Plan

1. **Identity/Session Foundation — high security risk, medium implementation risk.** Set exact recovery/session policy with owner; add Player, verifier, one-session generation, auth dependency, cookie/origin controls, non-enumerating errors and rate limits. Gate protected routes before Public exposure. Test new/returning device, duplicate names, expiry/logout/recovery revocation, direct API access.
2. **Player-Owned Save Migration — high data-loss risk.** Add player-scoped slot/active selection and owner predicates; preserve five-slot UI shape. Back up/copy legacy v4 data, define claim/discard policy, run transactional forward migration with ledger and rollback rehearsal. Test two-player isolation, overwrite, migration failure and restore. This follows identity because ownership needs a real Player ID.
3. **Battle Ownership/Reward Safety — high authorization/race risk.** Attach Player ID, immutable slot/profile, session generation and bounded lifetime to RAM sessions/attempts. Gate every lifecycle route; validate generation/ownership in the same transaction as receipt/reward. Test revocation, slot overwrite/switch, duplicate completion, Arena abandon, parallel attempts, and no-resume cleanup.
4. **Public Seed Enforcement/Diagnostics — medium compatibility risk.** Reject Public client seeds, draw/log effective server seeds, retain explicit Development seeds. Add server-only minimal diagnostics and retention/cleanup; no Public seed echo or full replay. Test Public direct HTTP rejection, Development deterministic runs and no mechanics drift.
5. **Frontend Onboarding/Recovery — medium UX/integration risk.** Add shared session-aware transport and initial/recovery/logout/code-regeneration flows ahead of existing slot UI. Validate cookie behavior, stale-session handling, refresh, mobile, and no secret in web storage. UI may be prototyped earlier but cannot be treated as security without phases 1–3.
6. **Integration/Public Release Validation — high release risk.** Use isolated migration fixture and Public DB, verify release artifact/route isolation, end-to-end two-player denial matrix, revocation races, backups/restores, TLS/origin/cookie behavior, single worker, rate limits and e2-micro capacity. Deployment is a separate approval gate.

This order is retained: foundational identity must precede ownership, which must precede safe rewards. Seed policy can be developed independently but is not a substitute for auth. The same combat rules/stats, one repository, Development deterministic tests and RELEASE-001 isolation remain invariant.

## 12. Required API and Database Changes

**API (proposal):** Add enrollment, recovery, current-session, logout and code-regeneration endpoints with a versioned contract; add an auth dependency to every player-owned route in the matrix. Keep existing player-facing slot numbers and response concepts where possible. Use consistent 401 for invalid/expired session, 403 or non-revealing 404 for foreign resource, 409 for genuine state conflict, and typed validation for forbidden Public seed. Do not accept Player ID, profile ID, seed, outcome or reward from a Public request as authority. Decide whether the generic battle route is Public supported or Development-only before changing it.

**SQLite (proposal):** Add `players` and protected recovery verifier, one active device session/reference with expiry and revocation/generation, player-scoped slots and active selection, unambiguous FK from profile to player/slot, and durable diagnostic metadata. Keep progression/receipt tables scoped to profile but enforce a join to authenticated player. Add unique constraints for `(player_id, slot_id)`, one active session, and one-time claim/migration receipts. Effective 256-bit battle seed should be stored as text/blob, not forced into SQLite signed 64-bit INTEGER. Define transaction lock order and migration idempotency before code. Current schema v4 is the starting point; do not mutate the actual local DB during design.

## 13. Testing and Acceptance Criteria

No tests were run for this read-only audit; these are **future implementation gates**:

- Two distinct players can each create/load five independent slots; neither can list, select, overwrite, launch from, or commit to the other's data, even with known IDs and direct HTTP calls.
- Duplicate Player Names do not collide; code recovery on a second device invalidates the first immediately; expiry/logout/regeneration reject old cookies; recovery errors do not reveal account existence and guessing is rate-limited.
- Battle state, commands, preview, completion and Arena operations all enforce immutable owner/session/launch slot. Revoke-vs-complete, overwrite-vs-complete, parallel attempts and duplicate receipt tests prove single reward application or rejection.
- Public generic/stage creation rejects a client seed; Arena and Public stage/generic seeds are server-owned; Development adapter/API deterministic tests remain reproducible. Server diagnostic seed is never in normal Public payloads.
- Browser refresh/close/disconnect cannot resume or reward an abandoned unfinished battle; cleanup/TTL is bounded. Confirm practical browser-close limitation in UX and server expiry tests.
- v4 legacy migration on a *copy* preserves claimed progress exactly, is idempotent, and rolls back on failure. Backup plus restore is exercised. Public build still excludes engineering routes, and Public/Development DB paths are distinct.
- Verify same-origin or credentialed CORS, Secure/HttpOnly/SameSite cookie, TLS, CSRF/origin checks, and realistic e2-micro disk/memory/write contention in the intended deployment. These cannot be established from source alone.

## 14. Open Questions Requiring Owner Decision

1. Confirm non-unique Player Names (this task's approved requirement) over the older document's “unique player/display name”; settle display-name normalization and duplicate-name recovery UX without making name a credential.
2. How may a current local save be claimed by an online Player ID, if at all? Which existing saves are owner progress versus test data, and who approves transfer? No automatic public import is safe.
3. What are recovery-code display/confirmation, regeneration/revocation, expiration and lost-code policies? Should generation revoke all prior sessions immediately? Set exact rate-limit and retention policy with security review.
4. Choose frontend/API deployment topology and cookie/CSRF policy: same-origin proxy preferred, or tightly configured cross-origin credential flow. Confirm actual DNS, TLS and origin list.
5. Is generic free-form `/api/v1/battles` a Public feature or Development-only compatibility route? This determines whether its seed-bearing contract is rejected or route-restricted.
6. Approve or adjust 30-day server-side diagnostic retention and permitted non-secret fields. Decide who can access diagnostics and how they are backed up/deleted.
7. Confirm battle abandonment grace/TTL, attempt capacity, one-worker operational model, backup frequency/restore objective, and e2-micro disk limits. Browser-close detection cannot be exact.

## 15. Final Readiness Assessment

**Audit complete; Public multi-player release is not ready.** RELEASE-001's engineering isolation is reusable, and SQLite can support a small single-instance pre-alpha if durable storage and backups are added. However identity, ownership, revocation, lifecycle cleanup, and Public seed restrictions are absent from the ordinary API, and production ingress/storage are unverified. Implement only under a separately approved task after the owner resolves Section 14. No app code, test, configuration, real save, commit, push or deployment change was made for this audit.

**Audit validation:** The 15 required sections and source references were checked against the current working tree; the independent reviewer found no blocking factual or security-severity issue. A whitespace/diff check of this new report found no formatting error. Existing tests were read as evidence only; no test suite, live browser/API call, database inspection, or infrastructure verification was performed.
