"""Isolated settings for fast payment unit tests; PostgreSQL is still required
for tests that exercise database locking or concurrent settlement behavior.
"""
import os

os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key")

from .settings import *  # noqa: F403,E402

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Fixtures opt into fake provider credentials explicitly; never inherit real keys.
PAYMONGO_ENABLED = False
PAYMONGO_SECRET_KEY = ''
PAYMONGO_SECRET_KEY_TEST = ''
PAYMONGO_SECRET_KEY_LIVE = ''
PAYMONGO_WEBHOOK_SECRET_TEST = ''
PAYMONGO_WEBHOOK_SECRET_LIVE = ''
