"""Tests: PostgreSQL 16 real y local (servicio `postgres-test` de docker-compose o servicio de CI).

Solo PostgreSQL y nunca Neon: se usa TEST_DATABASE_URL, jamás DATABASE_URL.
"""

import os
from urllib.parse import urlparse

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .local import *  # noqa: F403

DEFAULT_TEST_DATABASE_URL = "postgres://utrade:utrade@localhost:5433/utrade_test"
_test_database_url = os.getenv("TEST_DATABASE_URL") or DEFAULT_TEST_DATABASE_URL

_parsed = urlparse(_test_database_url)
if _parsed.scheme not in ("postgres", "postgresql"):
    raise ImproperlyConfigured("TEST_DATABASE_URL debe apuntar a PostgreSQL 16.")
if (_parsed.hostname or "").endswith("neon.tech"):
    raise ImproperlyConfigured(
        "TEST_DATABASE_URL no puede apuntar a Neon; usa el PostgreSQL local."
    )

DATABASES = {"default": dj_database_url.parse(_test_database_url, conn_max_age=0)}

SECRET_KEY = "django-insecure-test-only"
INTERNAL_PROXY_SECRET = "test-proxy-secret"
CRON_SECRET = "test-cron-secret"
OTP_SIGNING_SECRET = "test-otp-signing-secret"
EMAIL_PROVIDER = "console"
RESEND_API_KEY = ""

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "utrade-tests",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
FRONTEND_URL = "http://testserver-frontend"
