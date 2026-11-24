# Public deployment templates (not deployment authorization)

These are repository-managed templates and proposed procedures, **not an exact
copy of the live VM configuration**. The owner reported the first public HTTPS
deployment on 2026-11-19, with the start screen and API health reachable at
<https://loc-tactics.duckdns.org/>. The Owner subsequently authorized
`BATTLE_API_ENABLE_PUBLIC_BATTLES=1` on the installed VM and passed a manual
public core-gameplay journey with two complete battles. The repository template
still omits that flag and remains fail-closed by default; do not confuse the
template with the installed configuration. This is not final Public Alpha
acceptance. The canonical topology and acceptance record are
`docs/Technical/Public_Deployment_Runbook.md` and
`docs/Codex/Public_Core_Gameplay_Acceptance_2026-11-19.md`.
On 2026-11-20 the Owner also verified a **different installed backup setup**
and an isolated SQLite restore. Stage 1 Database Protection is complete within
the accepted local-backup Alpha scope. The installed `loct-db-backup` units,
script and schedule are documented in the canonical runbook; the templates
below are not a transcript of what runs on the VM.

## Required layout and permissions

- application release: `/opt/loct/current`, owned by the deployment account;
- Public database: `/var/lib/loct/public/player.sqlite3`, owner `loct`, mode
  `0600`; its directory mode `0700`;
- root-owned environment: `/etc/loct/public.env`, mode `0600`;
- local backups: `/var/backups/loct`, mode `0700`;
- one API worker only, loopback ports 8001/3001, Nginx as the sole network
  ingress. Uvicorn proxy-header rewriting stays disabled: FastAPI must see
  Nginx as the immediate peer, then `canonical_client_ip` validates the one
  Nginx-overwritten `X-Forwarded-For` value itself.

Generate independent 256-bit-or-stronger HMAC and rate-limit keys using the
approved secret manager/operator process. Never type them into shell history or
store them in Git. The recovery HMAC key and its version are required to recover
accounts after disaster; protect an encrypted copy separately from database
backups. A database backup without the matching key cannot verify Recovery
Codes.

## Clean initialization and inspection

Stop the API before initialization or offline upgrade. Create the durable
directory first, then initialize a new, absent database:

```sh
sudo -u loct /opt/loct/current/.venv/bin/python -m battle_api.init_public_db \
  /var/lib/loct/public/player.sqlite3
sudo -u loct /opt/loct/current/.venv/bin/python -m battle_api.public_db_ops \
  inspect --database /var/lib/loct/public/player.sqlite3
```

Inspection requires Public schema v5, `database_role=public`,
`public_battle_schema_revision=2`, and a full integrity check. Runtime does not
rewrite an older Public database.

For the narrowly supported Batch 1 Public-v5 foundation shape only, stop the
API and use the explicit backup-first offline command. It requires an exact
schema signature (including the existing lease/diagnostic/settlement
foundation tables), rejects any unknown/partial shape, and creates a separately
retained release backup before one atomic marker transaction:

```sh
sudo -u loct /opt/loct/current/.venv/bin/python -m battle_api.public_db_ops \
  upgrade-batch1-v5 \
  --database /var/lib/loct/public/player.sqlite3 \
  --backup-root /var/backups/loct \
  --confirm-offline-upgrade
```

Never point this command at Development data or an unverified copy. Local tests
use a modeled Batch 1 foundation (the authoritative Public-v5 shape with the
revision marker absent), not a real deployed legacy database. Inspection,
backup and rehearsal against a disposable copy of any actual legacy database
remain **BLOCKED pending a real authorized fixture** and are required before a
separately authorized deployment.

## Backups and isolated restore drill

The **repository template** runs SQLite's online backup API daily and retains
the newest seven files in `daily/`. A release backup is separately named and
is never removed by daily retention. These are not the installed VM unit names
or backup-script invocation; see the canonical runbook before operating on the
live server:

```sh
sudo -u loct /opt/loct/current/.venv/bin/python -m battle_api.public_db_ops \
  backup --database /var/lib/loct/public/player.sqlite3 \
  --backup-root /var/backups/loct --kind release --label RELEASE_IDENTIFIER
```

Each backup receives a SHA-256/metadata manifest and is integrity/schema
validated. Validate restoration only to a new isolated path:

```sh
sudo -u loct /opt/loct/current/.venv/bin/python -m battle_api.public_db_ops \
  restore-validate --backup /var/backups/loct/release/REQUIRED.sqlite3 \
  --destination /var/lib/loct/restore-drill/verification.sqlite3
```

The tool refuses to overwrite a destination. Delete the isolated drill copy
only after evidence is recorded. Do not replace the live database during a
drill and do not use raw file copying while WAL/writes may be active.

Off-VM GCS transfer would use `upload-backup-to-gcs.sh.template` only after
separate authorization and local verification. The Owner has **deferred GCS
for Pre-Alpha/Public Alpha to limit cost**; bucket setup, IAM, lifecycle,
upload/download and restore from GCS are **NOT IMPLEMENTED or verified**.
The accepted Alpha policy is local daily backups with seven-backup retention,
with the explicit residual risk that database and backups may be lost together
on the same VM/system disk. This is not a claim of full disaster recovery.

## Historical template release/rollback sequence — not the installed strategy

Stage 3 selected a **Single-Release Strategy** for Public Alpha: only one
deployed release is retained. The sequence below was a repository proposal
written before that decision and assumes a prior immutable release is
available for a symlink switch. **Do not apply it as the current VM rollback
procedure.** The Owner reports only basic rollback-readiness checks; no actual
rollback was performed. The first rollback test is deferred to a later release.
Before that release, document its actual upgrade/backup/recovery procedure
under the selected strategy and obtain the required authorization. See
`docs/Technical/Public_Deployment_Runbook.md` for the current decision and
accepted risks.

1. Confirm separate owner launch/deployment authorization.
2. Record health, schema inspection and current release identifier.
3. Stop API/web services and take a named release backup.
4. Validate its manifest and isolated restore.
5. Install a new immutable release directory, environment/templates, and
   dependencies; build/verify the Public artifact before switching `current`.
6. Run any approved offline database upgrade against the stopped database.
7. Start one API worker and web service; validate loopback health first, then
   Nginx HTTPS, cookie, Origin/CSRF, trusted proxy and route-isolation checks.
8. If application validation fails without a schema change, repoint `current`
   and restart. If schema changed, stop services and restore the verified
   pre-release backup only under the authorized recovery procedure. New writes
   after that backup cannot be preserved automatically.

The supplied Nginx, systemd, TLS paths, domain and GCS values are templates.
The reported live Web unit uses Vinext `--hostname`, while this repository's
`loct-web.service.template` still says `--host`; do not use it unchanged for a
fresh installation. The live VM has separate HTTPS and ACME Nginx files; this
repository's Nginx template includes an HTTP redirect whose live behavior is
not yet verified. The release-switch and rollback sequence above is historical
template material, not a tested VM rollback. Preserve these differences until separately
authorized configuration work reconciles them.
The installed database backup uses `/usr/local/bin/loct-db-backup` and
`loct-db-backup.service`/`.timer`, scheduled at 03:00 UTC with no randomized
delay. The repository backup templates instead use `loct-public-backup` unit
names, `public_db_ops`, and a 15-minute randomized delay. The installed backup
service has passed a manual systemd run and isolated SQLite restore, but
unattended execution, seven-file pruning and full application recovery remain
unverified.
The web unit verifies the Public artifact before launch and directs Wrangler's
log to systemd's writable `/var/log/loct` while keeping the release tree
read-only. Whether Vinext/Cloudflare needs any additional runtime-writable
state under the installed production versions is **NOT VERIFIED** and must be
tested under the unit sandbox before launch; do not weaken `ProtectSystem`
silently. `nginx -t`, service restart behavior, HTTPS/Secure cookies,
forwarding headers, firewall, log rotation, GCE resource limits and remote
backups also require deployment-environment validation.
