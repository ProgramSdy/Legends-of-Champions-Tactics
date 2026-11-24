# Stage 4.2.1 — Concurrent Battle Load Tester

**Status:** Authorized for local tool implementation and isolated verification only. No production load test or production write is authorized.

## Objective and boundaries

Build a small, maintainable Python tool under an appropriate testing directory to measure concurrent, independent Public-player 3v3 battle journeys. Support configurable concurrency, including 10, 30, 50 and 100 players; begin isolated verification at two players. A supported level is **not** permission to execute it on the GCE server. The earlier Stage 4 readiness plan proposed 2/5/10/20 live-player steps; this brief expands tool capability, not the approved live test sequence. Core must obtain separate Owner approval for the first production write and each subsequent load level or schedule.

Do not change game/application logic, deployment or GCE configuration, production data, rate limits, or security controls. Do not create paid cloud resources. Do not execute load tests against production during this task.

## Required preparation

Read `docs/README.md`, `docs/onboarding/ONBOARDING_SUMMARY.md`, `docs/Codex/Project_Rules.md`, `docs/Codex/Agent_Roles.md`, `docs/Codex/Current_Task.md`, the relevant role definitions, `docs/Technical/Architecture.md`, `docs/Technical/Player_Data_and_Save_System.md`, `docs/Technical/Public_Deployment_Runbook.md`, `docs/web-ui/BATTLE_DATA_CONTRACT_V1.md`, `docs/web-ui/PYTHON_ADAPTER_API.md`, and relevant RELEASE-002 Batch 1–3 reports. Inspect actual Public API routes, authentication/cookie/CSRF and session renewal, five-slot setup, structured Stage/Arena launch, battle state/preview/commands, terminal receipt/progression, SQLite access, Nginx rate-limit behavior, and existing load tests. Use actual contracts and legal battle actions; do not invent endpoints or payloads. Core must record proportional role selection and concrete ownership before implementation.

## Implementation

Create a Python CLI with minimal dependencies. Each simulated player must have a separate authenticated session, owned profile/save slot, and 3v3 battle. Exercise legitimate creation, turn/skill commands and a terminal outcome through normal Public API paths. Handle legal targets, action/command IDs, AI turns, battle completion and authoritative receipt according to the actual contracts. If reliable completion cannot be produced without changing gameplay or unsafe data setup, report that limitation; do not fake completed battles.

Measure request counts, average and P95 latency, throughput, error and timeout rates, and successful/failed battles. Provide a concise terminal summary and optional CSV without credentials, recovery codes or sensitive response bodies. Distinguish API failures, rate-limit responses, battle-rule rejections, capacity rejection and tool failures.

Provide configurable target URL, concurrency, request timeout, duration and global request-rate ceiling. Default to dry-run/non-production, performing no write requests. Production targeting must require unmistakable explicit opt-in flags and a separate Owner authorization; flags are safeguards, not authorization. No automatic ramp to higher concurrency. Begin at two players, bound requests and elapsed time, stop on excessive errors/timeouts, honor Nginx rate limits, and never evade CSRF, authentication, capacity or rate limiting. Avoid accidental targeting of the known public hostname by default, including via an alternate URL/redirect.

## Player-data safety gate

Never use real player accounts or their Recovery Codes. Prefer disposable local/isolated Public-mode database and dedicated test identities. Determine whether account creation, saves, battles, diagnostics and settlements leave permanent records, and document cleanup limitations. Do not delete, reset or overwrite production player data, and do not assume test accounts are removable. If safe isolated setup is unavailable, stop before any destructive workaround and report the blocker. The exact command proposed for a first two-player **production** trial must be supplied as a proposal only, with placeholders for approved test identities/configuration; do not run it.

## Verification and handoff

Verify locally or in an isolated environment where available: real request/response contracts and 3v3 rules, independent sessions and save ownership, metrics and CSV calculations, bounded time/rate/error stops, dry-run and production opt-in guards, credential redaction, and no impact on existing player data. Use disposable fixtures and record exact commands/results. Report script path/usage, real API workflow, account-isolation and permanent-record implications, local results, risks/blockers, and the proposed exact first two-player command. State clearly whether a production trial is safe to propose, **not performed**, and still awaiting Owner approval. Stop after tool implementation and local verification.
