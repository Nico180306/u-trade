"""Producción (Cloud Run / Render Free) contra Neon PostgreSQL 16 vía pooler (PgBouncer)."""

import os

import dj_database_url
import sentry_sdk
from django.core.exceptions import ImproperlyConfigured
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F403
from .base import env_list

DEBUG = False

_REQUIRED_ENV = (
    "SECRET_KEY",
    "INTERNAL_PROXY_SECRET",
    "CRON_SECRET",
    "OTP_SIGNING_SECRET",
    "RESEND_API_KEY",
)
for _required in _REQUIRED_ENV:
    if not os.getenv(_required):
        raise ImproperlyConfigured(f"Falta la variable de entorno obligatoria {_required}.")

SECRET_KEY = os.environ["SECRET_KEY"]
INTERNAL_PROXY_SECRET = os.environ["INTERNAL_PROXY_SECRET"]
CRON_SECRET = os.environ["CRON_SECRET"]
OTP_SIGNING_SECRET = os.environ["OTP_SIGNING_SECRET"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True

# Neon pooler (PgBouncer en modo transacción).
_database_url = os.getenv("DATABASE_URL")
if _database_url:
    DATABASES = {
        "default": dj_database_url.parse(_database_url, conn_max_age=0, ssl_require=True),
    }
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True

# WhiteNoise sirve los estáticos de /admin/.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Correo vía API HTTPS de Resend (apps.core.email, urllib estándar, timeout 5 s).
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "resend").strip().lower()

# Logs estructurados JSON a stdout.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "apps.core.log_formatters.JsonFormatter"}},
    "handlers": {"stdout": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["stdout"], "level": os.getenv("LOG_LEVEL", "INFO")},
}

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        traces_sample_rate=0.0,
        send_default_pii=False,
        # Sin variables locales en los frames: evita que códigos OTP o cuerpos de correo
        # lleguen a Sentry dentro de un traceback.
        include_local_variables=False,
    )
