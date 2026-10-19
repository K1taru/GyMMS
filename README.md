# GyMMS

GyMMS manages gym members, check-ins, membership pricing, cash receipts, and optional PayMongo QR Ph payments. It uses Django 5.2 LTS (`>=5.2,<5.3`), PostgreSQL 16, Gunicorn, and WhiteNoise. Dates use `Asia/Manila`.

Docker Compose runs three services: `db`, `web`, and `payment-worker`. Cloudflare Tunnel is managed separately; this repository does not deploy Cloudflare, Grafana, or Prometheus.

## First setup

Use Docker Engine with Compose on Linux. Raspberry Pi requires a 64-bit OS (`aarch64`), not a 32-bit ARM installation. Run commands from this repository's root.

```bash
cp .env.example .env
chmod 600 .env
```

Edit `.env`: choose a private database password and Django secret key. Generate a key with `python3 -c 'import secrets; print(secrets.token_urlsafe(64))'` and store it privately. Keep the local development settings for a local HTTP deployment. On an existing installation, edit its private `.env` in place; do not replace working values with the example.

```bash
docker compose config --quiet
docker compose up -d --build --wait
docker compose exec web python manage.py createsuperuser
docker compose ps
```

Open [the local app](http://localhost:8000/) or [Django admin](http://localhost:8000/admin/). Add a LAN hostname/IP to `DJANGO_ALLOWED_HOSTS` before using it from another device. `createsuperuser` creates an Owner with admin access; there is no seeded username or password. The web service waits for PostgreSQL, applies committed migrations, collects static assets, and starts Gunicorn. The worker starts after web's migration readiness check. Neither service creates users or seeds pricing.

Create pricing through the Owner interface, or optionally load the sample plans once:

```bash
docker compose exec web python manage.py seed_pricing
```

This command overwrites prices/labels and reactivates existing plans matching each sample duration. Multiple plans with the same duration can make it fail. Review existing plans before rerunning it; do not run it on every startup.

## One-time migration baseline reset

**Existing installations must reset their application database for this release.** Five fresh initial migrations replace the historical project migration chains. Old migration records are incompatible with this baseline. This discards the application's users, members, payments, and other database data; recreate your Owner afterward. Use this procedure only when that data is disposable. Fresh installations use the setup above.

Stop web and the worker before resetting, and keep them stopped until migration and Owner creation finish:

```bash
docker compose stop web payment-worker
docker compose build web payment-worker
docker compose up -d --wait db
```

Optional backup, written to a private local file, before discarding the database:

```bash
(umask 077; docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > gymms-before-baseline.dump)
```

Check that the dump command succeeded and retain the backup privately. The following reset targets only the configured application database inside the `db` service. It preserves the PostgreSQL volume, other databases, and the `media/` directory:

```bash
docker compose exec -T db sh -ec '
  case "$POSTGRES_DB" in ""|postgres|template0|template1) exit 1 ;; esac
  dropdb -U "$POSTGRES_USER" --maintenance-db=postgres --if-exists --force -- "$POSTGRES_DB"
  createdb -U "$POSTGRES_USER" --maintenance-db=postgres --owner="$POSTGRES_USER" -- "$POSTGRES_DB"
'
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py createsuperuser
docker compose up -d --wait web payment-worker
```

Do not use `docker compose down -v` or fake migration application. Do not repeat this reset for ordinary releases. Database backups belong to the migration history that created them; restoring an old dump also requires compatible application code/migrations.

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
| `DB_HOST`, `DB_PORT` | `db`, `5432` inside Compose; host access uses port `5433` |
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

The base images are `python:3.11-slim-bookworm` and `postgres:16-bookworm`. Compose leaves `platform` unset so Docker selects the host architecture. Build and run normally on a 64-bit Raspberry Pi; no x86 image override is required.

Optional cross-platform image build from a configured Buildx host:

```bash
docker buildx build --platform linux/arm64 --load -t gymms:arm64 .
docker image inspect gymms:arm64 --format '{{.Os}}/{{.Architecture}}'
```

This checks the built image's platform. Runtime startup, PostgreSQL connectivity, migrations, and payment behavior still need verification on the Pi. A native ARM64 deployment has not been validated by an x86 host without Docker.

## Routine maintenance

Back up PostgreSQL and `media/` before releases. After the baseline reset, future changes use ordinary reviewed, committed incremental migrations:

```bash
git pull
docker compose config --quiet
docker compose up -d --build --wait
docker compose exec web python manage.py migrate --check
docker compose logs --tail=100 web payment-worker
```

Keep logs private. Never run `makemigrations` during deployment or delete migration history to resolve a routine failure. When developing model changes, generate and review migrations locally, then commit them with the change.

## Tests

In a Python 3.11 virtual environment, install `requirements.txt`, then run the isolated SQLite suite:

```bash
python manage.py makemigrations --check --dry-run --settings=config.test_settings
python manage.py test --settings=config.test_settings
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
