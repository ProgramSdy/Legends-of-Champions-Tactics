# Current Task

**Status:** Completed

**Task:** RNG-001 — Fresh Randomness for Each Arena and Stage Battle Attempt

**Owner decision date:** 2026-10-20

## Objective

The owner chose fresh battle randomness for every new player-facing attempt:
each battle should feel like a fresh one. Apply this to Arena, Warrior's
Barrack, Paladin's Altar, and the common structured-stage launch path used by
future stages. A retry after defeat, draw, or resignation must not replay the
same random sequence merely because it is the same node and the player repeats
the same actions.

Keep the existing authoritative battle rules and predetermined Arena/stage
configuration. This changes the random seed of a **new attempt**, not the
ability to reproduce a deliberately seeded debug/test battle.

## Background and Evidence

Core's read-only investigation reproduced the owner's report: Arena retained
one persisted `battleSeed` per node, so identical retries produced identical
hero rolls, decisions, and a second Strike of Meteorite evade. The Mage's
11% ordinary agility-based evasion was legitimate; the problem is the retry
experience, not an incorrectly reported attack or a broken evade formula.

Arena launch currently passes the node seed to the battle registry. The normal
structured-stage Team Builder does not pass a seed; its backend accepts an
optional seed, and the unseeded adapter already creates fresh entropy. Verify
the complete live path and preserve existing working fresh behavior rather
than rewriting it unnecessarily.

## Requirements

1. Trace Arena and structured-stage creation, defeat/draw/resign/retry,
   replay of completed stages, reload and existing save-slot/run data. Record
   a concise design describing attempt creation, seed ownership, and relevant
   compatibility before implementation.
2. Ensure each deliberate new Arena node attempt receives a fresh,
   server-owned battle seed, including retry after loss, draw, or resignation.
   A changed seed must govern the battle's normal session RNG, including
   construction and combat randomness; do not reroll only evasion.
3. Verify the normal player-facing Warrior and Paladin structured-stage paths
   start each new attempt with fresh server-owned randomness, and ensure new
   stages using the shared structured launch path inherit that policy. Fix any
   path that accidentally reuses a seed. Do not apply this only to two named
   stage IDs or depend on a hard-coded hero/skill.
4. Preserve Arena's locked squad, persisted schedule, current node, enemy hero
   definitions, size and formations, as well as structured stages' fixed
   enemy definitions, formations, access/progression and rewards. Fresh
   battle randomness may naturally change generated hero names/stats and
   combat rolls; it does not guarantee every roll, name, or outcome differs.
5. Keep each individual running session internally deterministic for its own
   seed and event order. Preserve explicitly seeded debug/automated-test and
   intentional developer/API reproducibility as opt-in tools; the ordinary
   player-facing Arena/stage flow must not silently reuse a seed across new
   attempts. Keep server seed ownership and do not expose new player seed UI.
6. Do not treat ordinary updates, battle commands, render/reload of an already
   running session, or a mere transport retry as a new player-intended
   attempt. Audit current launch/error/retry behavior and use the smallest
   compatible safe approach to avoid unintended duplicate launches or
   progression; document any existing limitation or contract change. Do not
   silently claim exactly-once behavior that is not implemented.
7. Existing active/completed Arena runs and all save slots must remain
   loadable and retain their schedules, progress, rewards, and ownership. If a
   persistence migration is genuinely needed, make it safe, non-destructive,
   tested against existing schemas, and document it. The saved node seed must
   not continue to force identical combat retries.
8. Preserve server-side validation, victory-only/once-only progression,
   authoritative reward receipts, profile/slot isolation, cross-mode boundary,
   session RNG isolation, and concurrency locking. No changes to combat
   formulas, evasion chances, AI rules, or battle presentation are authorised.

## Out of Scope

- Altering Arena enemy schedule or stage curriculum, reset/abandon semantics,
  difficulty, hero definitions, unlocks, rewards, battle rules, or damage.
- Guaranteeing that a repeated attack hits or that every random result differs.
- Removing deliberate seeded debugging/reproducibility, exposing server seeds
  to players, client-owned combat RNG, or broad refactoring unrelated to
  attempt identity/seed generation.
- Commits, pushes, PRs, or other publication without separate owner approval.

## Relevant Files

- `battle_api/app.py`, `battle_api/adapter.py`, `battle_api/progression.py`,
  `battle_api/models.py` — Arena/stage launch, session RNG, seed input,
  persistence and profile-bound progression.
- `web-ui/components/battle/ArenaRunExperience.tsx`,
  `web-ui/components/battle/TeamBuilder.tsx`, structured-stage flow and
  `web-ui/lib/battle/liveProvider.ts` — intentional launch/retry/resign and
  client/server request boundaries.
- `tests/test_ui023_arena.py`, `tests/test_ui020_progression.py`,
  `tests/test_battle_adapter.py`, and relevant UI Arena/stage suites — update
  old same-node-same-seed retry assertions to the owner-approved fresh-attempt
  behaviour while retaining deterministic seeded tests.
- `docs/GDD/Game_Design_Document.md`, `docs/GDD/Combat_System.md`,
  `docs/Technical/Architecture.md`, `docs/Technical/Networking.md`,
  `docs/Technical/Player_Data_and_Save_System.md`,
  `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`,
  `docs/web-ui/PYTHON_ADAPTER_API.md`, `docs/web-ui/Screen_Flow.md`, and
  `docs/web-ui/WEB_UI_ARCHITECTURE.md` — update applicable stable rules,
  replacing claims that Arena combat seeds stay identical on retry.

## Acceptance Criteria

1. Intentional Arena retry after defeat, draw, and resign starts a new attempt
   with fresh server-side battle randomness, without regenerating the node's
   prescribed enemy definitions, battle size, formation, or run schedule.
2. Warrior Stage, Paladin Stage, and a representative shared/future-stage
   configuration use fresh randomness for each ordinary new attempt. Existing
   already-correct behavior remains intact.
3. Repeated use of a deliberately supplied identical test/debug seed remains
   reproducible, and distinct commands in a single battle advance the same
   session's existing RNG rather than reseeding every action.
4. Defeat/resign/draw do not advance or reset progress; victory and rewards
   remain authoritative and idempotent. Existing runs, saves, and unrelated
   profiles retain their data; intentional run abandonment remains separate.
5. Randomness is fresh per attempt, not a guarantee that any particular attack
   changes from miss to hit. No combat mechanic or evasion rule changes.
6. Documentation teaches this same player-facing policy for future stages,
   and precisely distinguishes session reproducibility/debug from retries.

## Validation Required

- Add deterministic tests that control/observe seed generation rather than
  relying on statistically different outcomes: two intentional retries get
  distinct attempt seeds and stable node configuration; test loss, draw,
  resign, ordinary reload/launch failure/transport-retry behavior and the
  original Warrior-versus-Mage scenario where feasible.
- Verify player-facing fresh behavior for both existing structured stages and
  their shared future-stage route; prove explicit equal-seed debug/test
  sessions are reproducible and per-session/global RNG isolation remains.
- Exercise active legacy Arena runs/save slots, migration if any, profile
  isolation, reward idempotency, completion concurrency and no progression on
  non-victory; ensure invalid launch does not corrupt state or consume a
  successful attempt unexpectedly.
- Run affected Arena/stage/progression, battle adapter/API/RNG, and frontend
  retry/resign suites, Python compilation, frontend typecheck/lint/build,
  `git diff --check`, and a meaningful manual Arena plus stage walkthrough if
  the environment permits. Record exact evidence and untested limitations.

## Agent Assignments

**Complexity/risk:** High cross-boundary gameplay/progression work: retry
identity, live RNG, persisted Arena nodes, stage launches, save compatibility,
and concurrency must remain correct. All five roles are selected.

- **project-manager:** coordinate design/attempt identity, role gate, scope,
  save and retry risk, documentation, and closure evidence.
- **game-engine-developer:** own seed lifecycle, session/adapter authority,
  API/progression compatibility and any minimal safe persistence change.
- **ui-developer:** audit Arena and structured-stage intentional launch,
  retry/resign/reload behavior and implement only necessary UI changes.
- **test-automator:** own deterministic retry/seed, save/progression,
  isolation/concurrency, and relevant frontend integration coverage.
- **reviewer:** independently assess fresh-attempt semantics, no duplicate
  sessions/progression, data safety, deliberate seeded reproducibility, and
  validation/contract evidence.

## Completion Notes — 2026-10-23

RNG-001 is complete and independently approved. Each intentional player-facing
Arena or structured-stage launch uses a new opaque attempt ID and fresh
server-owned session seed; process-local retries of the same creation request
reuse its original session. Existing Arena schedules and legacy saved node
seeds remain loadable without forcing combat retries to repeat. Explicitly
seeded debug/test launches remain reproducible. No persistence migration or
combat-formula change was needed.

The project-manager established the pre-code boundary; game-engine-developer
owned API/session identity and profile-safe idempotency; ui-developer audited
the intentional launch/retry boundary; test-automator supplied deterministic
backend and frontend coverage, including loss/draw retry; root integrated,
validated, and manually checked Arena and both structured stages. The
independent reviewer approved closure after the final loss/draw test.

Validation: backend Arena/stage/adapter/API suite 127 passed; focused frontend
RNG/UI-020 suite 15 passed; direct TypeScript check, ESLint (0 errors, 3
existing warnings), Vinext production build, Python compilation, and diff
check passed. A direct full frontend run had 437 passes and 15 failures;
comparison against a pre-RNG source archive reproduced the same 15 failures.
The npm wrapper's `content:check` is blocked by separately owner-edited Hero
Gallery YAML/generated content. Manual walkthrough on an isolated copy of the
progression database confirmed distinct Arena retry IDs/sessions and fresh
Warrior/Paladin stage launches; it did not claim direct browser visibility of
internal seed values. Automated checks cover those seed values and non-victory
progression behavior.

Remaining limitation: attempt idempotency and live sessions are process-local;
they are not durable across server restart or multiple workers. A browser
reload returns to the builder rather than recovering the in-memory session.

## Project-manager pre-code gate — 2026-10-20

**Complexity and risk:** High. This crosses the browser launch lifecycle,
FastAPI creation contracts, process-local battle sessions, persisted Arena
nodes, structured-stage launches, save-slot isolation, and deterministic RNG.
The main risks are a lost creation response accidentally starting another
battle, a deliberate retry reusing the old seed, changing fixed schedules or
legacy saves, weakening explicit-seed reproducibility, and claiming durable
exactly-once recovery that the current architecture does not provide.

**Actual role dispatch and ownership:** Wave 1 dispatched project-manager
(`rng001_pm`) for the design/risk/closure gate, game-engine-developer
(`rng001_engine`) for API/seed/idempotency authority, and ui-developer
(`rng001_ui`) for player launch identity and retry/resign/reload behavior.
All three began with read-only audits. The root coordinator owns integration,
documentation, and validation. After the project-manager delivered the gate
and freed a slot, wave 2 dispatched test-automator (`rng001_test`) for
deterministic backend/frontend tests. The four-slot concurrency limit requires
an independent reviewer wave. Wave 3 dispatched reviewer (`rng001_review`)
after the backend/UI changes landed; it owns read-only independent assessment
of the integrated boundary, tests, and documentation. Its findings remain
required for sign-off.

**Attempt boundary:** One intentional Enter Battle action creates one browser
`LiveBattleProvider` with one opaque `attemptId`. Creation retries by that
provider reuse the ID. After defeat, draw, or confirmed resign, the builder
returns; another intentional Enter creates a new provider and ID. Commands,
renders, presentation playback, and completion retries do not create an
attempt. A browser reload currently returns to the builder without restoring
the previous in-memory battle.

**Contract and seed ownership:** Add optional, backward-compatible request-body
`attemptId` to Arena-node and structured-stage creation; the normal player UI
always supplies it. Explicit developer/test stage or debug seeds remain
opt-in and reproducible. On the first accepted player-facing attempt, the
server draws fresh entropy once and passes that seed into the existing
session-isolated adapter RNG. Arena's persisted schedule, node index, battle
size, enemy definitions, formations, squad, completion, and legacy
`battle_seed` rows remain unchanged; the stored node seed ceases to drive new
combat attempts. Ordinary structured launches remain unseeded from the UI and
use the generic stage route, including future stages.

**Process-local retry safety:** The final implementation atomically binds each
`attemptId` globally to its original active profile, canonical
route/context/configuration fingerprint, and session/envelope. The same ID,
profile, and fingerprint returns the original
battle without another entropy draw. Reuse of an ID with a different route,
run/node/stage, ordered team, formation, or explicit seed yields a typed
conflict rather than an unrelated session. Do not mutate progression during
launch or alter victory-only/idempotent completion. Requests lacking
`attemptId` retain legacy per-POST behavior for API compatibility, so this is
not a universal exactly-once guarantee.

**Boundaries and gates:** The engine and UI roles must agree on the
`attemptId` field, fingerprint, conflict error, and process-local cache before
implementation. Tests must prove same-ID/same-config reuse without a second
seed draw, mismatch conflict, new-ID fresh seeds, loss/draw/resign new IDs,
and render/command/transport retry stability. Existing Arena rows and save
slots need no schema migration; preserve fixed node/stage configuration,
profile isolation, explicit-seed reproducibility, and rewards. Final sign-off
requires affected backend/frontend suites, compilation, typecheck, lint,
build, diff check, feasible manual walkthrough, documentation reconciliation,
and independent review.

**Honest limitation:** Sessions and attempt-idempotency cache are process-local.
Browser reload does not recover an old battle; server restart or multi-worker
deployment does not preserve this retry guarantee. Durable cross-restart or
cross-process exactly-once launch is not part of RNG-001.
