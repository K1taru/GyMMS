"""Opt-in PostgreSQL tests using explicit credentials, independent of .env DB data."""
import os
from .test_settings import *  # noqa: F401,F403

DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.environ.get('GYMMS_TEST_DB_NAME', 'gymms_payment_tests'),
    'USER': os.environ['GYMMS_TEST_DB_USER'],
    'PASSWORD': os.environ.get('GYMMS_TEST_DB_PASSWORD', ''),
    'HOST': os.environ.get('GYMMS_TEST_DB_HOST', '127.0.0.1'),
    'PORT': os.environ.get('GYMMS_TEST_DB_PORT', '55439'),
}}
