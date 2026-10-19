# GyMMS

GyMMS manages gym members, check-ins, membership pricing, cash receipts, and optional PayMongo QR Ph payments. It uses Python 3.14.8, Django 6.1.2, PostgreSQL 18.6, Psycopg 3, Gunicorn, and WhiteNoise. Runtime dependencies and their transitive dependencies are pinned in `requirements.txt`. Dates use `Asia/Manila`.

Docker Compose runs `db`, a one-shot `initialize` service, `web`, and `payment-worker`. Applications run as UID/GID `10001:10001`. Host-installed Cloudflare Tunnel connects to `http://127.0.0.1:8000`. See [Docker operations](docs/docker.md) for upgrades, backups, recovery, permissions, and troubleshooting. Cloudflare Tunnel is managed separately.

## First setup

Use Docker Engine with Compose on Linux. Raspberry Pi requires a 64-bit OS (`aarch64`), not a 32-bit ARM installation. Run commands from this repository's root.

```bash
cp .env.example .env
chmod 600 .env
sudo install -d -o 10001 -g 10001 -m 0750 media
```

Edit `.env`: choose a private database password and Django secret key. Generate a key with `python3 -c 'import secrets; print(secrets.token_urlsafe(64))'` and store it privately. Keep the local development settings for a local HTTP deployment. On an existing installation, edit its private `.env` in place; do not replace working values with the example.

```bash
docker compose config --quiet
docker compose build web
docker compose up -d --wait db
docker compose run --rm initialize
docker compose run --rm --no-deps web python manage.py createsuperuser
docker compose up -d --wait web payment-worker
docker compose ps
```

Open [the local app](http://localhost:8000/) or [Django admin](http://localhost:8000/admin/) on the Docker host; use the public tunnel hostname from other devices. `createsuperuser` creates an Owner with admin access; there is no seeded username or password. Initialization waits for a working database connection and applies committed migrations. Web collects static assets and starts Gunicorn; the worker starts after initialization succeeds and web responds to HTTP readiness probes. Startup does not create users or seed pricing.

Create pricing through the Owner interface, or optionally load the sample plans once:

```bash
docker compose exec web python manage.py seed_pricing
```

This command overwrites prices/labels and reactivates existing plans matching each sample duration. Multiple plans with the same duration can make it fail. Review existing plans before rerunning it; do not run it on every startup.

## Existing installations: PostgreSQL 18 cutover

This refresh starts with an empty PostgreSQL 18 database in a new `postgres18_data` volume. It does not import users, members, or payments from PostgreSQL 16. The previous volume and uploads are retained for recovery. Follow the [cutover procedure](docs/docker.md#cutover-from-postgresql-16) before starting this Compose configuration on an existing installation. Recreate the Owner and configure pricing afterward.

Fresh databases use the consolidated payment migration `0001_squashed_0002_processor_audit`, which creates the processor audit fields directly. The original payment migrations are retained so existing databases can finish pending upgrades and backfill processor identities. Django records applied migrations; subsequent initialization runs leave the schema and historical snapshots unchanged. Keep both original files until every deployed database has completed the upgrade. Future schema changes use incremental migrations. Never mount a PostgreSQL 16 data directory into PostgreSQL 18, delete migration history, or use `docker compose down -v` for upgrades.

## Configuration and HTTPS deployment

`.env.example` lists the supported variables. Keep `.env` private and out of Git. Canonical Django variable names use `DJANGO_*`.

| Variable | Meaning / local template value |
| --- | --- |
| `DJANGO_DEBUG` | `True` locally; `False` for public deployment |
| `DJANGO_SECRET_KEY` | Private generated key; required outside debug mode |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts without schemes; local `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated full origins; public example `https://gym.example.com` |
| `DJANGO_SECURE_SSL_REDIRECT` | `False` for local HTTP; `True` for public HTTPS |
| `DJANGO_SECURE_HSTS_SECONDS` | `31536000` when debug is off |
| `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS` | `True` when debug is off; requires HTTPS on subdomains |
| `DJANGO_SECURE_HSTS_PRELOAD` | `False` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Application database name and credentials |
| `DB_HOST`, `DB_PORT` | `db`, `5432` inside Compose; no database host port is published by default |
| `PAYMONGO_ENABLED`, `PAYMONGO_MODE` | `False`, `test` until payment setup is verified |
| `PAYMONGO_SECRET_KEY` | Optional fallback API secret for the selected mode |
| `PAYMONGO_SECRET_KEY_TEST`, `PAYMONGO_SECRET_KEY_LIVE` | Mode-specific API secrets; override fallback |
| `PAYMONGO_WEBHOOK_SECRET_TEST`, `PAYMONGO_WEBHOOK_SECRET_LIVE` | Separate endpoint signing secrets |
| `PAYMONGO_QR_EXPIRY_SECONDS` | `1800`; accepted range 60–9000 |
| `PAYMONGO_CONNECT_TIMEOUT`, `PAYMONGO_READ_TIMEOUT` | `5`, `15` seconds |
| `PAYMONGO_RECONCILE_INTERVAL` | `60` seconds |
| `PAYMONGO_WEBHOOK_TOLERANCE_SECONDS` | `300` seconds |

For public deployment, set debug off, a private Django key, your exact public hostname and HTTPS CSRF origin, and SSL redirect on. Cloudflare or another trusted proxy must terminate HTTPS and forward `X-Forwarded-Proto: https`. Restrict access to Gunicorn's origin so clients cannot forge this trusted header. Secure cookies and HSTS apply when debug is off. Preserve local development choices in your private environment; use these HTTPS overrides on the production host.

Configure and operate the external tunnel separately. See [the PayMongo deployment guide](docs/paymongo.md) before enabling QR checkout. Configuration changes require container recreation; restart alone does not reload the environment:

```bash
docker compose up -d --force-recreate --no-deps web payment-worker
docker compose exec web python manage.py check --deploy
docker compose exec web python manage.py check_paymongo --strict --production
```

The PayMongo production check is relevant once live payment configuration is installed. These checks do not prove provider connectivity. Updating `DB_PASSWORD` in `.env` does not change a password already stored in PostgreSQL.

## ARM64 builds

The base images are `python:3.14.8-slim-trixie` and `postgres:18.6-trixie`. Compose leaves `platform` unset so Docker selects the host architecture. Build and run on a 64-bit Raspberry Pi; no x86 image override is required. Dependency wheel resolution supports both AMD64 and ARM64; image builds and native startup still require Docker verification.

Optional cross-platform image build from a configured Buildx host:

```bash
docker buildx build --platform linux/arm64 --load -t gymms:arm64 .
docker image inspect gymms:arm64 --format '{{.Os}}/{{.Architecture}}'
```

This checks the built image's platform. Runtime startup, PostgreSQL connectivity, migrations, and payment behavior still need verification on the Pi. A native ARM64 deployment has not been validated by an x86 host without Docker.

## Routine maintenance

Back up PostgreSQL and `media/` before releases. Stop application services while applying schema changes; use reviewed, committed incremental migrations:

```bash
git pull
docker compose config --quiet
docker compose build web
docker compose stop web payment-worker
docker compose up -d --wait db
docker compose run --rm initialize
docker compose up -d --force-recreate --wait web payment-worker
docker compose exec web python manage.py migrate --check
docker compose logs --tail=100 web payment-worker
```

Keep logs private. Never run `makemigrations` during deployment or delete migration history to resolve a routine failure. When developing model changes, generate and review migrations locally, then commit them with the change.

## Tests

In a Python 3.14 virtual environment, install `requirements.txt`, then run the isolated SQLite suite:

```bash
python manage.py makemigrations --check --dry-run --settings=config.test_settings
python manage.py test --settings=config.test_settings
```

Run the QR payment widget cancellation/recovery checks with Node.js:

```bash
node --test --test-isolation=none tests/js/qr_payment.test.cjs
```

SQLite does not exercise PostgreSQL locking/concurrency. Use a dedicated disposable PostgreSQL cluster and a test role allowed to create databases. Set these test-specific values locally; never use production credentials:

```bash
export GYMMS_TEST_DB_USER=gymms_test
export GYMMS_TEST_DB_HOST=127.0.0.1
export GYMMS_TEST_DB_PORT=55439
export GYMMS_TEST_DB_NAME=gymms_payment_tests
read -rsp 'Dedicated test database password: ' GYMMS_TEST_DB_PASSWORD; echo
export GYMMS_TEST_DB_PASSWORD
python manage.py test --settings=config.postgres_test_settings
unset GYMMS_TEST_DB_PASSWORD
```

Django creates and drops a separate `test_` database. The tests use fake payment resources and do not call PayMongo. Verify fresh migrations against disposable PostgreSQL as well as running the suite.
