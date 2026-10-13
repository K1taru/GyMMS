# Imports
from pathlib import Path

import os
import environ


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read environment configuration before deriving security settings.
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
env = environ.Env(DEBUG=(bool, False))

DEBUG = env.bool("DJANGO_DEBUG", default=env.bool("DEBUG", default=False))
SECRET_KEY = env("DJANGO_SECRET_KEY", default="")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-local-development-only-change-me"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY must be set when DEBUG is false")

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"] if DEBUG else [],
)
if not DEBUG and not ALLOWED_HOSTS:
    raise RuntimeError("DJANGO_ALLOWED_HOSTS must be set when DEBUG is false")

# Cloudflare terminates TLS and forwards the original protocol in this header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
        "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True
    )
    SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    # GyMMS apps
    "core",
    "dashboard",
    "memberships",
    "metrics",
    "payments",
    "users",
    
    "crispy_forms",          # Better form rendering
    "django_filters",        # Filtering for lists
    "django_extensions",     # Dev utils

]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [ BASE_DIR / "templates" ],     # Configured
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='gymms_db'),
        'USER': env('DB_USER', default='gymms_user'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# PayMongo QR Ph configuration. Secrets are selected by mode by the payment
# service; keeping them here avoids logging or exposing them in application UI.
PAYMONGO_ENABLED = env.bool("PAYMONGO_ENABLED", default=False)
PAYMONGO_MODE = env("PAYMONGO_MODE", default="test").lower()
if PAYMONGO_MODE not in {"test", "live"}:
    raise RuntimeError("PAYMONGO_MODE must be either 'test' or 'live'")
PAYMONGO_SECRET_KEY = env("PAYMONGO_SECRET_KEY", default="")
PAYMONGO_SECRET_KEY_TEST = env("PAYMONGO_SECRET_KEY_TEST", default="")
PAYMONGO_SECRET_KEY_LIVE = env("PAYMONGO_SECRET_KEY_LIVE", default="")
PAYMONGO_WEBHOOK_SECRET_TEST = env("PAYMONGO_WEBHOOK_SECRET_TEST", default="")
PAYMONGO_WEBHOOK_SECRET_LIVE = env("PAYMONGO_WEBHOOK_SECRET_LIVE", default="")
PAYMONGO_QR_EXPIRY_SECONDS = env.int("PAYMONGO_QR_EXPIRY_SECONDS", default=1800)
if not 60 <= PAYMONGO_QR_EXPIRY_SECONDS <= 9000:
    raise RuntimeError("PAYMONGO_QR_EXPIRY_SECONDS must be between 60 and 9000")
PAYMONGO_CONNECT_TIMEOUT = env.int("PAYMONGO_CONNECT_TIMEOUT", default=5)
PAYMONGO_READ_TIMEOUT = env.int("PAYMONGO_READ_TIMEOUT", default=15)
PAYMONGO_RECONCILE_INTERVAL = env.int("PAYMONGO_RECONCILE_INTERVAL", default=60)
PAYMONGO_WEBHOOK_TOLERANCE_SECONDS = env.int(
    "PAYMONGO_WEBHOOK_TOLERANCE_SECONDS", default=300
)
if min(PAYMONGO_CONNECT_TIMEOUT, PAYMONGO_READ_TIMEOUT, PAYMONGO_RECONCILE_INTERVAL,
       PAYMONGO_WEBHOOK_TOLERANCE_SECONDS) <= 0:
    raise RuntimeError("PayMongo timeouts, reconciliation interval, and signature tolerance must be positive")


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_USER_MODEL = 'users.StaffUser'

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Manila"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"

#STATICFILES_DIRS = [
#    BASE_DIR / "static",
#    ]    # For global static/
STATIC_ROOT = BASE_DIR / "staticfiles"      # For collectstatic (deployment)

MEDIA_URL = "/media/"                       # Media directory
MEDIA_ROOT = BASE_DIR / "media"             # Uploaded files

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication settings
LOGIN_URL = 'core:login'  # Redirect to login page if not authenticated
LOGIN_REDIRECT_URL = 'dashboard:dashboard'  # Redirect after successful login
LOGOUT_REDIRECT_URL = 'core:index'  # Redirect after logout

