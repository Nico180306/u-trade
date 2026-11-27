"""Producción (Cloud Run / Render Free) contra Neon PostgreSQL 16 vía pooler (PgBouncer)."""

import os

import dj_database_url
import sentry_sdk
from django.core.exceptions import ImproperlyConfigured
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F403
from .base import env_list

DEBUG = False

for _required in ("SECRET_KEY", "INTERNAL_PROXY_SECRET", "CRON_SECRET"):
    if not os.getenv(_required):
        raise ImproperlyConfigured(f"Falta la variable de entorno obligatoria {_required}.")

SECRET_KEY = os.environ["SECRET_KEY"]
INTERNAL_PROXY_SECRET = os.environ["INTERNAL_PROXY_SECRET"]
CRON_SECRET = os.environ["CRON_SECRET"]

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

# Correo vía SMTP de Resend (sin dependencias nuevas).
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.resend.com"
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = "resend"
EMAIL_HOST_PASSWORD = os.getenv("RESEND_API_KEY", "")
EMAIL_TIMEOUT = 10

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
    )
