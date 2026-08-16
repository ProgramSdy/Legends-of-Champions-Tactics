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
There is no implemented resume, reconnect, handoff, save, or recovery path;
the Player Data and Save System remains future work.

## Security Considerations

Local development CORS is restricted to the configured browser origin. The
adapter accepts only typed public request/command schemas and must not trust
client claims about positions, legal targets, damage, or outcomes. This project
does not yet implement authentication, authorization, encrypted production
transport, abuse controls, or multiplayer anti-cheat; those are future design
requirements, not completed features.

## Change Log

- 2026-08-15 — Documented the current versioned battle-session transport and
  its UI-018/UI-019 formation fields, authority, and limitations.
- 2026-07-26 — Initial document created.
