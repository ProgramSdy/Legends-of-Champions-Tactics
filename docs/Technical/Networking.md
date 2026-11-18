# Networking

## Purpose

Authoritative networking design and constraints.

## Current Status

Implemented local-development HTTP boundary: a Next.js client communicates
with the FastAPI battle adapter. This is a request/response battle-session
transport, not a multiplayer, WebSocket, or persistent-session network design.

## Network Model

The browser creates a battle with `POST /api/v1/battles`, receives an
authoritative versioned envelope, then submits version-checked commands to the
session endpoints. The adapter process holds active sessions in memory.
Requests can include an optional seed for reproducible composition and
computer-formation selection within that session. A refresh, process restart,
or multi-worker deployment does not provide recovery or shared session state.

Arena-node and structured-stage creation accept an optional opaque
`attemptId`. The normal player UI sends one ID per intentional Enter Battle
and reuses it for a transport retry by the same provider. Within the current
adapter process, a profile-bound identical ID and launch configuration returns
the original session/envelope without another seed draw; using the ID with a
different route or configuration returns HTTP 409 `battleAttemptConflict`.
Omitting the ID preserves legacy per-POST creation semantics. This is
process-local retry safety, not durable exactly-once creation: a server restart
or multi-worker deployment cannot recover the binding. Browser reload does not
resume an active battle; a later explicit Enter Battle is a new attempt.

In Development, save selection is the existing anonymous five-slot
request/response flow. In the isolated Public Batch 1 backend,
`GET /api/v1/save-slots` lists the authenticated player's five slots; create,
load, and confirmed overwrite mutate only that player's owned profile and
active-slot selection. The browser does not submit a Player ID or profile ID
as authority. Public session authentication, saved-code acknowledgment,
Origin, and CSRF checks gate those endpoints.

Arena Run uses dedicated profile-bound endpoints. The browser may read run
state, submit the initial six-member squad, launch only the current node with
its friendly team/formation, and commit an ended friendly victory. It never
submits node seeds, enemy teams, progression, or completion outcomes. The
browser may also abandon a run only by posting its server-issued run ID to the
profile-scoped abandon endpoint after explicit player confirmation; the server
deletes the active profile's matching run and returns the new Arena state.
After the twelfth committed victory, the UI acknowledges the persisted completed
state and routes to Stage Map. A later Arena visit uses that completed state
only to authorize the replacement-squad flow; it does not display the former
completion page again or create a run without an explicit squad request.
A separate `/api/v1/debug/battles` route accepts free-form development battles
without reading or mutating save/progression data.

Engineering battle creation is registered only when the server process starts
with exact `LOCT_RELEASE_MODE=development`. Missing, blank, invalid, and
explicit `public` mode omit that route from routing and OpenAPI; a direct POST
receives 404. Local `make dev`, `make backend`, and `make lan` explicitly select
Development; `make backend-public` explicitly selects Public. The setting is
server-owned and cannot be changed by a client request. RELEASE-002 Batch 2
retains a default-off Public battle gate: without exact server-side
`BATTLE_API_ENABLE_PUBLIC_BATTLES=1`, every Public battle route is absent from
routing/OpenAPI. Isolated Batch 2 test processes may opt in to owner-bound
Stage/Arena launch, state, command, preview, Resign, and receipt routes.
Generic and Engineering Debug battle creation remain absent in Public even
with that opt-in. Development retains its ordinary battle routes. The opt-in
is a test boundary, not permission to deploy player-facing Public battles.

## Protocols and Interfaces

The public contract is HTTP JSON, currently `contractVersion: "1.0"`.
Authoritative request, command, snapshot, event, and error shapes are defined
in `web-ui/PYTHON_ADAPTER_API.md` and `web-ui/BATTLE_DATA_CONTRACT_V1.md`.

Formation fields are creation-time, size-discriminated values:

- 2v2: `front-rear` or `side-by-side`.
- 3v3: `one-front-two-rear`, `two-front-one-rear`, or `all-front`.
- 1v1: no formation fields.

The friendly formation is required in 2v2/3v3. A player-controlled enemy also
sends a matching-size formation. A computer-controlled enemy omits its
formation; the adapter chooses it from the session-seeded random stream and
returns the actual choice in `snapshot.formations` plus each combatant's
authoritative `position`.

## Synchronisation and Authority

Commands include the expected adapter revision. The adapter rejects stale or
invalid commands and returns the authoritative snapshot/revision needed for
client reconciliation. `turnControl` and `legalActions` define command
ownership and selectable targets. The client uses these facts for interaction
only; it does not perform local target legality, AI, damage, or formation
calculation.

Battlefield visual depth is deliberately not a networked combat field. It is a
deterministic frontend interpretation of the returned 3v3 formation, side, and
ordered slot; `front`/`rear` remains the networked engine position.

## Error Handling and Recovery

The client distinguishes disconnected, adapter, rejected, and stale-command
failures and provides retry at the appropriate boundary. Creation validation
rejects missing/invalid/wrong-size formation values rather than coercing them.
Persistent progression reloads through an occupied slot, but there is no
implemented live-battle resume, reconnect, handoff, backup, or recovery path.
If the active slot changes after a structured battle launches, completion is
rejected rather than committed to another profile.
The same launch-profile guard applies to Arena completion.

## Security Considerations

Local Development CORS is restricted to configured browser origins. Public
Batch 1 adds server-owned Player ID, Recovery Code verification, one active
device session, per-player save ownership, exact Origin and session-bound CSRF
checks on unsafe requests, and persistent recovery-abuse limiting. The
authentication cookie is host-only `Secure; HttpOnly; SameSite=Lax`; Public
requires explicit separate database and identity configuration. This is a
backend boundary, not proof that the required same-origin HTTPS reverse proxy,
global rate control, backup/restore, client onboarding, or battle lifecycle is
deployed. Public health fails closed when required identity/storage is absent.
Authenticated GET requests validate without changing session expiry or token;
the Origin/CSRF-protected `POST /api/v1/sessions/refresh` renews the sliding
30-day session and may rotate its credential. A missing Public database is
created only through the separate one-time `python -m battle_api.init_public_db`
initializer, never by API startup.
The Public frontend now uses same-origin credentialed requests with an
in-memory CSRF token. The one-time Recovery Code is not browser-persisted;
session and five-slot authority remain server-side. An explicit protected
refresh POST may renew a near-expiry session; ordinary GET/preview/playback
does not. A 401 invalidates local player views, whereas CSRF 403 revalidates
the session read-only and never replays the rejected mutation. Player-facing
Manual formation data uses this same-origin boundary. Development retains
its localhost adapter URL. Normal Public battle access stays closed by
default. The isolated Public Stage/Arena launch
contract rejects a `seed` field even when its value is `null`; the server
generates the effective 256-bit combat seed and retains it only in diagnostics.
Development generic/Stage/Debug explicit seeds remain supported. A healthy
isolated backend test does not verify the future HTTPS/proxy/player UX gates.

Public deployment templates require one Nginx ingress, one FastAPI worker,
loopback services, Uvicorn `--no-proxy-headers`, and one Nginx-overwritten
`X-Forwarded-For` address from an exact trusted peer. Local self-signed HTTPS
and a development proxy do not verify real certificate, firewall or Nginx
behavior. Public health and identity fail closed if the configured DB/schema,
exact HTTPS Origin, trusted proxy or distinct strong HMAC keys are absent.

## Change Log

- 2026-11-18 — Added Batch 3 same-origin Public frontend, read-only session
  revalidation, explicit refresh, and deployment-only proxy caveat.
- 2026-11-17 — Documented the RELEASE-002 Batch 2 default-off Public battle
  route gate, isolated owner-bound paths, and mode-specific seed boundary.
- 2026-11-16 — Documented RELEASE-002 Batch 1 Public identity, save
  ownership, fail-closed configuration, and complete Public battle-route gate.
- 2026-11-10 — Added fail-closed Development/Public Release debug-route
  registration and clarified the remaining identity and seed-policy boundary.
- 2026-08-15 — Documented the current versioned battle-session transport and
  its UI-018/UI-019 formation fields, authority, and limitations.
- 2026-08-20 — Added the local five-slot HTTP boundary and clarified that it is
  shared adapter state, not authentication, cloud save, or session recovery.
- 2026-08-31 — Added typed Arena Run and isolated debug-battle routes; neither
  weakens ordinary roster ownership validation.
- 2026-07-26 — Initial document created.
