#!/usr/bin/env bash
# CI only: test a built image against the disposable PostgreSQL service.
set -euo pipefail
image=${1:?image reference required}
platform=${2:-linux/amd64}
docker run --rm --platform "$platform" "$image" sh -ec '
  pip check
  python manage.py makemigrations --check --dry-run --settings=config.test_settings
  python manage.py test --settings=config.test_settings
'
docker run --rm --platform "$platform" --network host \
  -e GYMMS_TEST_DB_NAME=gymms_ci \
  -e GYMMS_TEST_DB_USER=gymms_ci \
  -e GYMMS_TEST_DB_PASSWORD=ci-only-password \
  -e GYMMS_TEST_DB_HOST=127.0.0.1 \
  -e GYMMS_TEST_DB_PORT=5432 \
  "$image" sh -ec '
    python manage.py migrate --noinput --settings=config.postgres_test_settings
    python manage.py test --settings=config.postgres_test_settings
  '
