# Public HTTPS Deployment and Operations Runbook

## Status and evidence boundary

**19 November 2026 — first public HTTPS deployment and core-gameplay acceptance achieved.** The Owner reports external API health, browser rendering, and two complete public battles at <https://loc-tactics.duckdns.org/>. The later gameplay acceptance followed explicit Owner authorization to set `BATTLE_API_ENABLE_PUBLIC_BATTLES=1` on the installed VM. **Stages 1–4 are accepted for their defined Public Alpha scope; final Alpha launch readiness remains PENDING.** The dated gameplay test record is `docs/Codex/Public_Core_Gameplay_Acceptance_2026-11-19.md`.

Deployment results and live-host values in this runbook come from the Owner's 19–23 November handovers and the Stage 4 implementation report. Documentation synchronization inspected the local repository, **not** the live VM. The server-side Nginx and systemd files were changed manually and may differ from repository templates. Stage 3 outcomes are Owner-reported; no detailed Nginx rules, rate-limit thresholds, or test transcript was supplied in that handover. Stage 4 measurements come from the recorded production runs, not an independent rerun during this documentation closeout. Statements marked *pending* require later verification.

## Installed topology and release identity

| Component | Owner-reported installed state |
| --- | --- |
| GCE VM | `legends-of-champions-tactics-server`, `us-central1-a`, `e2-micro`, Ubuntu 24.04.5 LTS; external IPv4 `35.208.207.139` |
| Public address | `loc-tactics.duckdns.org` (Duck DNS); HTTPS TCP 443, HTTP TCP 80 for ACME |
| Release | `RELEASE-003-db7f3395`, Git commit `db7f3395`, `/opt/loct/releases/RELEASE-003-db7f3395` |
| Active pointer | `/opt/loct/current`; Python environment `/opt/loct/current/.venv`; web root `/opt/loct/current/web-ui` |
| API | `loct-api.service`, `/etc/systemd/system/loct-api.service`, FastAPI/Uvicorn on `127.0.0.1:8001`, user `loct` |
| Web | `loct-web.service`, `/etc/systemd/system/loct-web.service`, Vinext on `127.0.0.1:3001`, user `loct` |
| Edge | Nginx 1.24.0 (Ubuntu), `/etc/nginx/conf.d/loct-https.conf` and `/etc/nginx/conf.d/loct-acme.conf` |
| Public state | `/etc/loct/public.env` (root-owned, restricted); `/var/lib/loct/public/player.sqlite3` |

The Owner's `systemctl is-active loct-api loct-web nginx` check returned `active` for all three. Subsequent controlled API/Web process-kill tests confirmed `Restart=on-failure` recovery, but actual restart-after-VM-reboot behavior is still pending. The VM has approximately 953 MiB RAM. Stage 4 changed the configured active-battle ceiling from 20 to **200** through a separately authorized environment-only change; **30**, not 200, is the maximum observed simultaneous active-battle count.

The release-directory/current-symlink layout is installed, but Stage 3 selected a **Single-Release Strategy**: only one deployed release is retained. `deploy/public/README.md` contains an earlier multi-release switch/rollback proposal, not the current tested VM procedure. **No actual rollback has been performed.**

The developer accesses the VM by SSH as `programsdy` from an Apple Silicon Mac mini; the reported local key path is `~/.ssh/loct_gce`. This is a local private-key location, not a repository artifact. Never copy the key, Duck DNS token, Certbot account data, HMAC keys, session material, or `/etc/loct/public.env` contents into Git or support logs.

For an authorized operator with access to that key, the expected SSH form is `ssh -i ~/.ssh/loct_gce programsdy@35.208.207.139`; this is a documented access pattern, **not** a command executed during this documentation update. Confirm the VM identity and host key before accepting a new SSH host key. Avoid including environment-file values in captured output.

## Routing and network exposure

```text
External browser -- HTTPS 443 --> GCE firewall --> Nginx
                                              /api/* --> 127.0.0.1:8001 (FastAPI)
                                              other  --> 127.0.0.1:3001 (Vinext)
```

The reported HTTPS Nginx configuration uses the Duck DNS hostname, TLS, a 1 MB request-body limit, a 65-second proxy-read timeout, `X-Forwarded-Proto: https`, and an `X-Forwarded-For` value overwritten with `$remote_addr`. `sudo nginx -t` passed and the configuration loaded. API and Web bind only to loopback; ports 8001 and 3001 are not intended public ingress. A separate Nginx endpoint at `127.0.0.1:8080` was used for local-only reverse-proxy testing. Direct access to Vinext on port 3001 is **not** a valid end-to-end test: it does not proxy `/api/`, so same-origin API requests return 404.

The VM network tag is `loct-web`. Reported GCE ingress rules `loct-allow-http` and `loct-allow-https` permit TCP 80 and 443 respectively from `0.0.0.0/0` to that tag. External HTTPS health access verified the 443 path; a future exposure audit should confirm no unintended public access to 3001/8001 or other ports.

HTTP port 80 uses `/etc/nginx/conf.d/loct-acme.conf` to serve HTTP-01 files from `/var/www/letsencrypt`. **HTTP-to-HTTPS redirect behavior has not been verified.** Do not claim that all HTTP requests redirect.

## DNS, TLS and public configuration

Duck DNS resolved `loc-tactics.duckdns.org` externally to `35.208.207.139`. Let's Encrypt issued the certificate on 19 November 2026, expiring 17 February 2027. The reported certificate paths are `/etc/letsencrypt/live/loc-tactics.duckdns.org/fullchain.pem` and `privkey.pem`. Certbot 2.9.0 used webroot HTTP-01; the challenge file was reachable from both the VM and external Mac mini. In Stage 3 the Owner reported HTTPS/TLS acceptance and a **passed Certbot renewal dry-run**. An actual unattended renewal and post-renewal Nginx reload have **not** been reported as tested; HTTP-to-HTTPS redirect behavior was not specified in the Stage 3 handover.

The reported `/etc/loct/public.env` includes `LOCT_RELEASE_MODE=public`, `LOCT_BUILD_VERSION=RELEASE-003-db7f3395`, `BATTLE_API_PUBLIC_DB=/var/lib/loct/public/player.sqlite3`, and `BATTLE_API_PUBLIC_ORIGIN=https://loc-tactics.duckdns.org`. Other sensitive values are deliberately omitted here. The Public database was initialized and its schema integrity checked. On 20 November, local backup and independent database-level restore passed within the Owner-approved Alpha scope; see the next section. Full application disaster recovery remains untested. Never copy Development saves into the Public database.

`battle_api/public_config.py` enforces a valid HTTPS Public origin. An earlier HTTP localhost origin prevented API startup; the owner changed it to the final HTTPS hostname before external testing. Changing the origin requires the normal protected configuration and service-restart procedure; do not edit it for an ad hoc browser test. The **source-code default** for Public Battle is off, but after the Owner's separate authorization the **installed VM** has `BATTLE_API_ENABLE_PUBLIC_BATTLES=1` in `/etc/loct/public.env`. A pre-change configuration backup was reported at `/etc/loct/public.env.pre-battle.bak`. Following an API restart, the route gate admitted owner-bound Stage/Arena battle routes. The initial Stage launch 404 was the expected disabled-gate behavior, not an edge-routing defect; see the dated acceptance record. Do not confuse the configuration backup with a tested database backup or rollback.

## Stage 1 — Database Protection (Alpha Scope), completed 20 November 2026

The following are **Owner-reported live-VM checks**, not commands rerun during this documentation update. The GCP project is `legends-of-champions-tactics`. The production database `/var/lib/loct/public/player.sqlite3` is owned by `loct:loct`, has mode `0600`, uses SQLite journal mode `delete`, and returned `ok` from `PRAGMA integrity_check`.

The installed backup implementation is `/usr/local/bin/loct-db-backup`, writing timestamped SQLite snapshots under `/var/backups/loct/`. The installed units are `/etc/systemd/system/loct-db-backup.service` and `/etc/systemd/system/loct-db-backup.timer`; the service runs as `loct:loct` with `WorkingDirectory=/`, `UMask=0077`, and `NoNewPrivileges=true`. It uses SQLite `.backup` for an online, consistent snapshot, checks each candidate with `PRAGMA integrity_check`, and does not publish a temporary file that fails integrity checking. The service was manually started through systemd and returned `Result=success`, `ExecMainStatus=0`.

The enabled timer is scheduled daily at **03:00 UTC**, with `Persistent=true` and `RandomizedDelaySec=0`. Its first observed next execution was 21 November 2026 at 03:00 UTC; this is a point-in-time observation, **not evidence that the unattended scheduled run has happened**. Local retention is configured for the seven newest timestamped backups. Retention syntax and normal execution passed, but deletion when more than seven files exist has **not** been tested.

Four mode-`0600` backup files of approximately 228 KB each were observed on 20 November: `player-20261120-062208.sqlite3`, `player-20261120-062421.sqlite3`, `player-20261120-062648.sqlite3`, and `player-20261120-063027.sqlite3`. A snapshot passed SQLite integrity checking and contained two player rows. In a separate database-level restore drill, `player-20261120-063027.sqlite3` was copied to `/tmp/loct-restore-test/restored.sqlite3`; that copy returned `PRAGMA integrity_check = ok` and `SELECT COUNT(*) FROM players = 2`. The temporary copy and test directory were then removed. **The production database was not overwritten.** This proves an isolated SQLite restore/read, not application-level recovery or a full disaster-recovery procedure.

Current operator procedure, as evidenced by the handover: let the enabled timer invoke the installed backup service, confirm successful service result and a new protected snapshot, verify its integrity, and restore-test only by copying a selected snapshot to a separate disposable path and checking integrity and expected records. Never restore over `/var/lib/loct/public/player.sqlite3` during a test. This document does not invent the installed script's CLI flags; inspect that script and unit on the VM before changing or manually invoking them. Keep the database, backups, and sensitive account material out of shared logs and Git.

The VM has **Deletion Protection enabled** and its boot-disk deletion rule is **Keep disk**. These settings reduce accidental deletion risk but are not independent backups. The Owner explicitly **deferred Google Cloud Storage/off-server backup for Pre-Alpha/Public Alpha to minimize cost**. The accepted Alpha policy is local daily SQLite backups with seven-backup rolling retention. The accepted residual risk is that the production database and all local snapshots occupy the same VM/system disk and may be lost together. GCS, bucket-scoped IAM, off-server lifecycle retention, freshness alerts and application-level disaster-recovery testing are future improvements, **not implemented or verified**. Stage 1 is complete only within that limited Alpha policy; Stage 2 results follow below.

**Repository/VM drift:** `deploy/public/loct-public-backup.service.template` and `.timer.template` use `loct-public-backup` unit names, `WorkingDirectory=/opt/loct/current`, a `public_db_ops` command and a timer with `RandomizedDelaySec=15m`. The installed VM instead uses the `loct-db-backup` units, standalone script, `/` working directory, exact 03:00 UTC schedule and zero randomized delay. `deploy/public/README.md` describes the repository template workflow, not the installed VM's backup procedure. Do not silently substitute either for the other.

## Stage 2 — Operational Stability, completed for defined checks on 20 November 2026

These are **Owner-reported VM observations and controlled tests**, not checks rerun by this documentation task. Stage 2 completion does not certify sustained load, automatic browser reconnection, security hardening, disaster recovery, or Alpha launch readiness.

### Resources and service recovery

- RAM was approximately **953 MiB**. No OOM events were found in the inspected **48-hour journal window**; this does not predict behavior under concurrent load.
- Root disk usage was initially **84%**, with about **1.5 GB** available. Significant Snap cache use was identified. The operator removed only **single-link Snap cache files**, preserving hard-linked files and installed Snap packages. Root usage then measured **69%**, with about **2.8 GB** available. API, Web, Nginx and HTTPS remained operational. No VM upgrade or extra cloud service was needed. This records a completed, narrowly scoped cleanup, not a general instruction to delete Snap files in later releases.
- `loct-api` and `loct-web` are enabled systemd services with `Restart=on-failure` and `RestartSec=5`. Both passed controlled **SIGKILL** recovery tests and restarted automatically. Browser refresh restored normal operation after transient upstream failures; Nginx did not need a restart. **In-progress battle recovery, automatic browser reconnection, VM reboot recovery and long-running stability were not tested.**

### Journal and error observations

The installed `/etc/systemd/journald.conf.d/60-loct-alpha.conf` sets `Storage=persistent`, `SystemMaxUse=150M`, `SystemKeepFree=1G`, and `MaxRetentionSec=14day`. The Owner reports a successful `systemd-journald` restart, verified effective configuration and active service. Journal usage fell from approximately **295.9 MB to 74.7 MB** without a manual vacuum; API and Web logs remained accessible. This is installed-server configuration, not a repository-managed file.

Two Web errors merit monitoring, without a proven root cause:

| UTC observation | Evidence | What is not established |
| --- | --- | --- |
| 05:49 | Vinext logged `server reference not found 'x'`; an external `POST /` returned HTTP 500. | Why the server reference was missing, whether the request represented a normal player, and whether the issue recurs. |
| 07:19 | Vinext logged static-file `Premature close` errors correlated with asset requests from a client identifying itself as `ClaudeBot`. | The client's actual identity or the precise cause of the premature close. |

Nginx upstream connection errors around **08:10 and 08:14 UTC** matched the controlled API/Web termination tests; they are expected test effects, not evidence of an unrelated outage.

### External traffic and limited security checks

At inspection, `access.log` held **2,859 requests**; two IP addresses accounted for about **92%**. Many requests targeted common sensitive paths such as `.env`, `phpinfo.php`, Docker Compose and WordPress files. This pattern **strongly suggests generic automated scanning**, but client identities and intent were not proven. Direct HTTPS checks of `/.env`, `/.env.production`, `/docker-compose.yml`, `/appsettings.json`, and `/laravel/.env` each returned **404**. These five checks are not a comprehensive security audit. **No IP blocking or rate limiting was implemented during Stage 2**; the later Stage 3 hardening and tested rate limit are recorded immediately below.

## Stage 3 — Security and Release Management, Owner-accepted for Public Alpha

The Owner reports the following Stage 3 closeout. These are **Owner-reported operational results and acceptance decisions**, not checks rerun by this documentation task. The handover does not include exact installed Nginx rules, rate-limit values, firewall rule inventory, or detailed test commands; do not infer them from repository templates.

| Area | Accepted result | Boundary |
| --- | --- | --- |
| 3.1 Nginx hardening | Completed. | The precise installed directives were not supplied here; preserve the actual server configuration as the source of truth. |
| 3.2 Rate limiting | Completed and tested. | Thresholds, scope and test evidence were not supplied; no numeric policy is asserted here. |
| 3.3 HTTPS/TLS | Completed; Certbot renewal dry-run passed. | A dry-run is not an actual certificate renewal or proof of post-renewal Nginx reload. |
| 3.4 SSH/firewall | Reviewed; remaining exposure accepted. | Public TCP 22 remains reachable and uses key authentication. Do not describe SSH as closed to the internet. |
| 3.5 Release management | Existing deployment procedure reviewed; **Single-Release Strategy selected**. | Only one deployed release is retained. The repository's multi-directory rollback proposal is not the current tested VM procedure. |
| 3.6 Rollback readiness | Basic checks completed. | **No actual rollback was performed**; defer the first real rollback test to the next release. |
| 3.7 Security acceptance | Accepted by Owner for Public Alpha. | This is a stage decision, not a claim that every Alpha launch or load gate is complete. |

**Accepted residual risks:** (1) public SSH port 22 with key authentication; (2) one retained deployed release and no demonstrated rollback yet; (3) daily local SQLite backups with seven retained copies but no off-server copy. The database and local backups can be lost together with the VM/system disk. These are explicit Owner decisions for Public Alpha, not controls verified away by Stage 3.

**Current release-management boundary:** `/opt/loct/current` still names the active release, but only one deployed release is retained under the selected Single-Release Strategy. `deploy/public/README.md` contains a historical multi-release switch/rollback proposal; it is not an executed or approved same-VM rollback instruction for the current strategy. Before a later upgrade, document the actual install, database backup and recovery steps for that release and perform the deferred rollback test if authorized. Do not claim a prior release is available locally for an immediate symlink rollback.

## Stage 4 — Performance and Load Testing, Owner-accepted / closed 23 November 2026

The recorded bounded production runs used **10, 20 and 30 dedicated players** in a 2v2 Warrior's Barrack Stage 1 scenario at about **3 global requests/second**. Stage A (10) settled 52/52 battles; Stage B (20) settled 42/42. The first 30-selected-player attempt settled 43/43 started battles but only **20/30** workers participated, so it failed its participation gate. Preserve that result as a real unsuccessful attempt, superseded for the final outcome by the separately authorized rerun.

Before the rerun, the Owner authorized changing `BATTLE_API_PUBLIC_BATTLE_CAPACITY` from **20 to 200** in the protected environment file and restarting only `loct-api`. An initial health probe saw a transient 502 during restart; subsequent health and service checks passed. The final run initialized 30/30 players, started and settled one battle for each (30/30), and a read-only server snapshot independently observed **30 simultaneous active leases**. The battle phase issued **291 requests in 97.83 seconds**, achieved **2.97 RPS**, and recorded **925.91 ms average / 1,089.96 ms P95** battle API latency, with zero unexpected HTTP 429, API/tool errors, timeouts or unfinished battles. Post-run checks found 30/30 dedicated accounts ready and eligible, zero active battle leases, active API/Web/Nginx services and a healthy API. The exact evidence and earlier attempts are in `docs/Codex/Stage_4_2_1_Implementation_Report.md`.

**Accepted limits:** 200 is a configured ceiling, not demonstrated sustainable capacity; 30 leases is the maximum observed. The final battle phase ended before the 300-second window. CPU/memory/I/O samples were sparse, not continuous endurance or SQLite high-concurrency integrity proof. The e2-micro remains resource-constrained; 50/100-player figures are estimates only, with no production trials. No further Stage 4 load test is authorized by closure. The next gate is the **Final Public Alpha Launch Readiness Review** and explicit Owner go/no-go decision, not automatic launch.

## Reported verification and useful checks

The following results were **reported in the owner handover**, not rerun during this documentation update:

| Check | Reported result | Limit |
| --- | --- | --- |
| `systemctl is-active loct-api loct-web nginx` | `active` × 3 | One-time state, not reboot resilience |
| `sudo nginx -t` | Passed | Not a full HTTP redirect or certificate-renewal test |
| VM: `curl -i --resolve loc-tactics.duckdns.org:443:127.0.0.1 https://loc-tactics.duckdns.org/api/v1/health` | HTTP 200; `{"status":"ok","contractVersion":"1.0"}` | Internal HTTPS path |
| Mac mini: `curl -i --connect-timeout 8 https://loc-tactics.duckdns.org/api/v1/health` | HTTP 200; same JSON | External HTTPS API path |
| Chrome on external Mac mini: public root URL | Logo, fantasy artwork, START GAME button, expected layout rendered | Infrastructure check only; later gameplay acceptance is recorded separately |
| Chrome on external Mac mini: core player journey | New player, Recovery Code, Save Slot, World Map, two structured battles, exit/reload progress passed | Manual Owner test; not restart, multi-player, load or full Alpha acceptance |

For future operational checks, the installed unit names and config paths above identify where to inspect service state and logs. The repository contains the unit templates and database operation commands in `deploy/public/README.md`; inspect the installed unit before assuming its `ExecStart` or sandbox is identical. Do not run database restore against the live path as a health check.

Suggested **read-only** operator checks for a later acceptance session (not claimed as executed here) are `systemctl status loct-api loct-web nginx`, `journalctl -u loct-api -u loct-web -u nginx --since today`, `sudo nginx -t`, and the external health request above. Review logs for sensitive values before sharing them. Stage 3's Certbot renewal dry-run passed; a later operator should verify the actual unattended renewal and Nginx reload rather than treat the dry-run as that evidence. For SQLite, inspect the installed backup units/script and protected backup directory before relying on a repository-template command; never overwrite the live database during a drill.

## Provisioning sequence and troubleshooting record

The reported successful sequence was: configure Duck DNS → open TCP 80 → configure ACME webroot → verify challenge externally → obtain certificate → configure HTTPS Nginx → set final API Public origin → restart API and reload Nginx → verify internal HTTPS → open TCP 443 → verify external HTTPS → load the browser start screen. For a later release, verify each prerequisite against the current VM; this sequence is historical knowledge, not blanket approval to redeploy.

- The first Web unit used unsupported Vinext `--host`; the installed command was corrected to `--hostname` to bind loopback. **Repository drift:** `deploy/public/loct-web.service.template` still uses `--host`. Correct that template in a separately authorized implementation task before relying on it for a fresh install.
- Public API startup failed with an HTTP localhost `BATTLE_API_PUBLIC_ORIGIN`; Public configuration requires HTTPS. The final origin uses the Duck DNS domain.
- An SSH tunnel to the Web port displayed the player entry screen but `/api/` returned 404. Test the complete product through Nginx, which owns same-origin API routing.
- Static asset permissions and macOS-generated file metadata required manual correction during release preparation. The repository does not encode a confirmed permanent fix or enough detail to reproduce the exact repair; inspect and document it before the next release.
- The public edge was initially unreachable because TCP 80/443 ingress rules were absent. The rules were added; the external HTTPS health request then succeeded.
- **Nginx template drift:** `deploy/public/nginx-loct.conf.template` contains a combined port-80 redirect/port-443 TLS configuration, whereas the reported VM uses separate HTTPS and ACME files. The live HTTP redirect is unverified. Whether this split is intentional long-term is undecided; never assume the template was installed unchanged.

## Public Alpha acceptance still open

1. **Functional beyond the tested path:** second-device recovery and revocation, cross-player ownership isolation, Hero Gallery/asset coverage, Arena and other battle modes, API error handling and broader client/browser scenarios. The first public account/slot/structured-battle/reload journey passed manually; do not reset it to untested.
2. **After Stage 3 — operational follow-up:** Observe the first unattended backup and seven-file pruning; monitor backup freshness, disk/RAM/OOM and Vinext errors; verify API/VM restart persistence and in-progress battle behavior. The Owner accepted Nginx hardening, rate limiting and a Certbot dry-run, but actual renewal/reload, HTTP redirect, full application recovery and detailed proxy/Origin/CSRF evidence remain separate checks. Public SSH and local-only backups are accepted Alpha risks, not absent exposures.
3. **Release and performance:** Stage 4 is Owner-accepted within the bounded 10/20/30-player scope above. Retain its endurance, higher-load and SQLite limits for ongoing operations; alpha tester onboarding, update procedure under the Single-Release Strategy, the first actual rollback test at a future release, bug reporting, feedback and itch.io instructions remain for the final review or later work. Do not claim rollback or disaster recovery before a witnessed drill.

Track evidence and blocking status in `docs/Codex/RELEASE_002_Public_Launch_Readiness_Checklist.md`. Stages 1–4 are accepted within their defined scope; the final Alpha launch decision remains separate and pending.
