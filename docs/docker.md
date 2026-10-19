# Docker deployment and operations

## Deployment layout

Use a 64-bit Raspberry Pi OS with Docker Engine and current Docker Compose v2 supporting `service_completed_successfully` and `--wait`. Host-installed cloudflared connects to `http://127.0.0.1:8000`. The web port binds to loopback only; PostgreSQL has no published port. Applications connect to `db:5432` on the Compose network.

The shared application image uses Python 3.14.8 on Debian Trixie, Django 6.1.2, Psycopg 3, Gunicorn, and WhiteNoise. PostgreSQL uses `18.6-trixie`. Versions are explicit; refresh pins deliberately and rerun checks rather than using `latest` tags. The Dockerfile uses BuildKit dependency caching. `requirements.txt` pins all runtime and transitive dependencies; unused REST framework, Bootstrap crispy adapter, and python-dotenv packages were removed after source inspection.

Startup order: PostgreSQL health check → successful `initialize` (real connection retry and migrations) → web static collection and Gunicorn → HTTP/database readiness → payment worker. A migration failure blocks dependent startup. During routine releases, explicitly run initialization before replacing application containers, as shown in the README; do not rely on an old completed initialization container to migrate a new release.

`GET /health/` returns `200 {"status": "ok"}` or `503 {"status": "unavailable"}` and disables caching. It is the only route exempted from HTTPS redirection. The container probe uses the first configured allowed host; it never calls PayMongo. An unhealthy flag does not automatically restart a running container: restart policy handles process exits. Check worker logs and provider delivery separately.

## Configuration and writable files

Keep existing private `.env` values; `DB_USER=postgres` remains supported. This username is independent of the Linux UID used by application containers. The official PostgreSQL image makes `POSTGRES_USER` a database superuser on initial creation, even if named `gymms_user`; a limited database role requires explicit grants. Environment edits do not change existing database roles or passwords.

Only database settings reach the database container. Application containers run as `10001:10001`, drop Linux capabilities, disallow privilege escalation, and receive a 60-second shutdown grace period. The worker stops claiming new jobs after SIGTERM and finishes current work; a provider operation exceeding the grace period may be terminated and must recover through existing durable job handling.

Create the upload directory before the first startup:

```bash
sudo install -d -o 10001 -g 10001 -m 0750 media
```

For an existing upload tree, inspect it and back it up first, then adjust ownership of that specific tree with `sudo chown -R 10001:10001 ./media`. A bind mount overrides image directory permissions. Do not apply recursive permissions to the repository or other host directories. Static files live inside the web container and regenerate on startup; uploads persist on the host. No shared static volume is required.

Default memory limits: web 1 GiB, worker 512 MiB, database 1 GiB; initialization 512 MiB while migrating. Allow additional RAM for the OS, tunnel, and Docker. Gunicorn starts two workers with two threads each. Tune these Compose limits and worker counts based on `docker stats`, out-of-memory logs, and measured load. Logs rotate at 10 MiB with three files per service.

For local database tools, create a private Compose override containing:

```yaml
services:
  db:
    ports:
      - "127.0.0.1:5433:5432"
```

Run it with `docker compose -f docker-compose.yml -f docker-compose.local.yml up -d db`. Host clients use `127.0.0.1:5433`; Django still uses `db:5432`. For remote administration prefer an SSH tunnel rather than publishing database or Gunicorn ports publicly.

## Cutover from PostgreSQL 16

This is an intentional fresh start. Users, members, pricing, and payment history are not imported. Keep uploads, backups, the old configuration, old image, and PostgreSQL 16 volume. Never attach PostgreSQL 16 storage to PostgreSQL 18. The new volume key is `postgres18_data`, mounted at `/var/lib/postgresql`; PostgreSQL 18 uses `/var/lib/postgresql/18/docker` internally. See the [official image's storage guidance](https://hub.docker.com/_/postgres).

Perform the following preparation while the old release is still installed:

1. Schedule downtime. Set `PAYMONGO_ENABLED=False` and recreate old web/worker. Keep the old webhook route and worker running until all outstanding provider attempts and events are resolved. If unresolved real payments remain, postpone the fresh start.
2. Record the old Git revision, Compose project name (`docker compose ls`), exact database volume (`docker volume inspect`), environment file, and database/application image IDs. Preserve the existing application image under a private rollback tag. Save private copies of the old Compose file and `.env` outside the repository; backup files must not be committed or included in image builds.
3. Stop old web and worker to freeze writes. Leave the old database running while backing it up:

```bash
docker compose stop web payment-worker
(umask 077; docker compose exec -T db sh -ec 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > gymms-before-pg18.dump)
(umask 077; docker compose exec -T db sh -ec 'pg_dumpall -U "$POSTGRES_USER" --globals-only' > gymms-before-pg18-globals.sql)
(umask 077; tar -czf gymms-before-pg18-media.tar.gz media)
```

Check each exit status. Inspect the archive with `pg_restore --list` using PostgreSQL 16 tooling, and test restoring it into a separate disposable PostgreSQL 16 database. Listing alone is not a restore test. Inspect the media archive with `tar -tzf`. Store copies securely outside the deployment host.

4. Stop the old database. Install the new release in the same deployment directory and keep the same Compose project name. Preserve the private `.env`; set production Django security values and leave payments disabled. Prepare upload ownership as described above. The old volume must stay untouched. Do not run `down -v`, `volume prune`, or delete volumes.
5. Validate, build, initialize PostgreSQL 18, and create a new Owner before opening access:

```bash
docker compose config --quiet
docker compose build web
docker compose up -d --wait db
docker compose run --rm initialize
docker compose run --rm --no-deps web python manage.py createsuperuser
docker compose up -d --wait web payment-worker
docker compose exec web python manage.py check --deploy
docker compose exec web python manage.py migrate --check
docker compose exec web python manage.py check_readiness
docker compose exec web python manage.py check_paymongo
docker compose ps -a
```

If old explicitly named containers conflict, stop and remove only those obsolete containers after recording their mounts; never remove their volumes. Configure pricing through the Owner interface, or deliberately use the optional `seed_pricing` command described in the README. Verify login, new member creation, upload persistence, cash payments, static assets, and worker operation. Follow the PayMongo guide before enabling QR checkout. Keep the public tunnel inaccessible during this verification.

## Recovery and routine releases

Before accepting new writes, rollback can stop the new web/worker/database and restore the old release's configuration and image with its original PostgreSQL 16 volume and project name. The new PostgreSQL 18 volume must remain separate. Verify old database contents and media permissions before restoring traffic. Restoring old database backups requires the matching old application and migration history.

After accepting records or payments on the new database, reverting to the old volume would lose those new records. Disable collection and reconcile provider state before planning recovery. Preserve both volumes and payment evidence; do not silently reopen an older database. A database backup cannot undo external provider payments.

For subsequent releases follow the README maintenance sequence: backup, build, stop web/worker, run initialization, recreate web/worker, verify readiness. For environment-only changes use `docker compose up -d --force-recreate --no-deps web payment-worker`; restart alone retains old environment values. Keep secrets out of rendered Compose output and logs; `config --quiet` validates without printing them.

## Troubleshooting and validation

- Failed initialization: inspect `docker compose logs --tail=100 initialize db`. The wait command tries 30 real connections with two seconds between failures and a five-second per-connection timeout. Invalid credentials fail within bounded retries without printing them. Correct the configuration, rerun initialization, then start web/worker.
- Web unhealthy: inspect web logs and run `docker compose exec web python manage.py check_readiness`. Check database connectivity, allowed hosts, migrations, and static directory permissions. `/health/` failure returns no private diagnostics.
- Upload denied: verify host ownership is `10001:10001`, directory traversal permissions, disk space, and read-only mount flags. Test through the member upload UI; do not make the entire project world-writable.
- Worker stops: inspect worker logs and database status. A graceful stop should finish the current operation and exit before 60 seconds. An unhealthy web dependency gates startup only; it does not supervise the worker after startup.
- Resource pressure: use `docker stats` and inspect container exit/OOM status before adjusting memory or Gunicorn concurrency.

On a Docker-capable host, verify `docker compose config --quiet`, fresh migrations, health success/failure, failed initialization blocking web/worker, bad credentials, read-only media failure, shutdown, and record persistence across restart. Run the SQLite suite and PostgreSQL concurrency suite against a disposable PostgreSQL 18 cluster with explicit `GYMMS_TEST_DB_*` credentials.

Build both architectures with a configured Buildx builder:

```bash
docker buildx build --platform linux/amd64 --load -t gymms:test-amd64 .
docker buildx build --platform linux/arm64 --load -t gymms:test-arm64 .
```

Cross-building requires appropriate emulation or native builders. A successful cross-build is not native Pi runtime verification. Native ARM64 startup and checks remain necessary. No Docker daemon is available in the implementation workspace, so container builds, PostgreSQL 18 integration, memory limits, mount permissions, and native Pi startup must be verified on the deployment/test host before cutover.

Implementation verification (October 19, 2026): on Python 3.14.8 with the pinned dependencies, 64 tests passed and four PostgreSQL concurrency tests were skipped. Migration drift and dependency consistency checks passed. Dependency wheel resolution/metadata confirmed Python 3.14 AMD64 and ARM64 support. A local Gunicorn smoke test verified HTTP readiness with HTTPS redirection enabled and a clean SIGTERM shutdown. Production Django checks with fixture settings emitted only the expected HSTS preload warning; strict offline PayMongo checks passed with fixture credentials. These checks made no provider requests and did not modify production data.
