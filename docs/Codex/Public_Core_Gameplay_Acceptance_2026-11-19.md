# First Public End-to-End Gameplay Acceptance — 19 November 2026

**Classification: Public Deployment Core Gameplay Acceptance — PASSED.** This is a dated manual acceptance record for `RELEASE-003-db7f3395` at <https://loc-tactics.duckdns.org/>. It does **not** approve a full production release or certify Public Alpha launch readiness.

## Evidence boundary

The project Owner supplied the test and server-operation observations in the 19 November 2026 handover. Testing was performed in Chrome on an external Mac mini against the public HTTPS GCE deployment, not the local development environment. This documentation task checked the repository's release-route gate but did not access the VM, rerun browser tests, or independently inspect server logs, OpenAPI, cookies, or the database. No credentials, Recovery Codes, tokens, or private configuration values are recorded here.

The deployed environment is GCE VM `legends-of-champions-tactics-server` (`us-central1-a`, e2-micro, Ubuntu 24.04 LTS), Duck DNS, Let's Encrypt TLS, Nginx HTTPS ingress, `loct-api.service` (FastAPI/Uvicorn on `127.0.0.1:8001`), `loct-web.service` (Vinext on `127.0.0.1:3001`), and Public SQLite. The canonical topology and operational details are in `docs/Technical/Public_Deployment_Runbook.md`.

## Public Battle activation and the initial 404

The initial structured launch `POST /api/v1/stages/warriors-barrack/battles/1` returned HTTP 404. The Owner's investigation found the route implemented in `battle_api/app.py` but absent from the running OpenAPI specification. Repository inspection confirms `_apply_release_route_gate()` removes every `/battles` route in Public mode unless the server process starts with exact `BATTLE_API_ENABLE_PUBLIC_BATTLES=1`. The 404 was therefore the intended fail-closed route gate, **not** an Nginx, TLS, or generic API-routing failure.

After the Owner explicitly authorized activation, the server-side `/etc/loct/public.env` was updated to include `BATTLE_API_ENABLE_PUBLIC_BATTLES=1`; a pre-change backup was made at `/etc/loct/public.env.pre-battle.bak`. The Owner reports that `loct-api.service` was restarted, remained `active (running)`, Public configuration validation passed, and `public_battles_enabled` was `true`. The running OpenAPI then included Stage launch, battle state, commands, preview, Resign, completion, and Arena battle routes. The original launch 404 was resolved **without application-code changes**. This is a reported live-server change, not a file modification by this documentation task.

The source-code default remains fail-closed for a new Public process without the flag. The **installed VM** is now explicitly opted in; it must no longer be described as having Public Battle disabled. This approval covered activation for the reported acceptance test; it is not proof that all security, capacity or operational release gates passed.

## Owner-reported manual results

| Test area | Result |
| --- | --- |
| Public HTTPS access and start screen | PASS |
| New player creation | PASS |
| Recovery Code generation and saving | PASS |
| Save Slot creation | PASS |
| World Map loading | PASS |
| Browser refresh and session continuity | PASS |
| Return to start screen; load existing Save Slot | PASS |
| Structured Training Battle formation screen | PASS |
| Public Battle initialization and arena rendering | PASS |
| Hero and enemy teams; round and turn initialization | PASS |
| Skill execution; skill and status-effect display; battle progression | PASS |
| Two complete battles | PASS |
| Exit and reload saved progress | PASS |
| Functional consistency with Mac mini development environment | PASS — Owner's manual observation in tested scenarios |

The Owner reports normal behavior in both battles, including skill execution and status displays. Completed progress remained available after normal game exit and reload. This supports **application-level persistence across normal exit/reload**, not persistence after API/VM restart or database restore. It also does not establish behavior for other players, concurrent battles, all battle sizes, every skill, Arena completion, second-device recovery, or fault scenarios.

## Remaining Pre-Alpha work

1. Verify automated SQLite backup, retention, off-VM copy and isolated restore on the deployed host.
2. Measure memory, CPU, disk, latency and capacity on the e2-micro under realistic multi-player and concurrent-battle load.
3. Complete security, rate-limit, proxy/header, permissions, logging and operational-stability checks.
4. Rehearse deployment upgrade and rollback without risking live player data.
5. Verify save and settled-reward persistence after API and VM restart.
6. Test multiple player identities, ownership isolation and concurrent battles through public HTTPS.
7. Complete the final Alpha release-readiness review and obtain the relevant owner authorization.
8. Prepare itch.io Alpha distribution and tester instructions.

Further open items from the earlier infrastructure milestone include HTTP-to-HTTPS behavior, certificate renewal and Nginx reload, reboot recovery, and documented differences between repository templates and installed service/Nginx files. The live configuration backup named above is **not** a verified rollback or database backup.

**Subsequent progress (20 November 2026):** Stage 1 Database Protection passed within the Owner-approved local-backup Alpha scope, including an isolated SQLite restore. The 19 November pending list above is retained as a dated snapshot; current backup status, accepted same-disk risk and remaining operational checks are in `docs/Technical/Public_Deployment_Runbook.md` and the release-readiness checklist.

## Milestone decision

**2026-11-19 — First Successful Public End-to-End Gameplay Test.** The Owner verified the core player journey from account creation and Save Slot management through World Map navigation, structured battle execution, and persisted progression on the public HTTPS deployment. **Public Deployment Core Gameplay Acceptance: PASSED.** Final Public Alpha readiness remains **PENDING**; see `docs/Codex/RELEASE_002_Public_Launch_Readiness_Checklist.md` for the outstanding gates.
