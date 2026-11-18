# Public deployment templates (not deployment authorization)

These files are reviewed templates for a future single-VM Pre-Alpha deployment.
They have not been installed on GCE, exercised with a real domain/certificate,
or used to expose Public players. `BATTLE_API_ENABLE_PUBLIC_BATTLES` is
deliberately absent so battle access remains default-off.

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

The systemd timer runs SQLite's online backup API daily and retains the newest
seven files in `daily/`. A release backup is separately named and is never
removed by daily retention:

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

Off-VM GCS transfer uses `upload-backup-to-gcs.sh.template` only after local
verification (copy it to an operator-only path and set mode `0700` first).
Bucket name, service-account permissions, encryption, lifecycle,
upload/download, and restore from GCS are **NOT VERIFIED** here and block Public
launch until tested on the real deployment environment.

## Release and rollback sequence

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
The web unit verifies the Public artifact before launch and directs Wrangler's
log to systemd's writable `/var/log/loct` while keeping the release tree
read-only. Whether Vinext/Cloudflare needs any additional runtime-writable
state under the installed production versions is **NOT VERIFIED** and must be
tested under the unit sandbox before launch; do not weaken `ProtectSystem`
silently. `nginx -t`, service restart behavior, HTTPS/Secure cookies,
forwarding headers, firewall, log rotation, GCE resource limits and remote
backups also require deployment-environment validation.
