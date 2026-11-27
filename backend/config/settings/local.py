"""Desarrollo local (runserver / docker compose `backend`) contra la rama development de Neon.

`backend/.env` se carga SOLO cuando este es el módulo de settings activo, de modo que
`test.py` (que hereda de aquí) y `production.py` nunca leen ese archivo.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

if os.getenv("DJANGO_SETTINGS_MODULE") == "config.settings.local":
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=False)

import dj_database_url  # noqa: E402

from .base import *  # noqa: E402, F403
from .base import env_list  # noqa: E402

DEBUG = True
SECRET_KEY = os.getenv("SECRET_KEY") or "django-insecure-local-only-change-me"
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "http://localhost:5173")

INTERNAL_PROXY_SECRET = os.getenv("INTERNAL_PROXY_SECRET") or "dev-local-proxy-secret"
CRON_SECRET = os.getenv("CRON_SECRET") or "dev-local-cron-secret"
OTP_SIGNING_SECRET = os.getenv("OTP_SIGNING_SECRET") or "dev-local-otp-signing-secret"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Sin base de datos de respaldo: si falta DATABASE_URL, Django falla en la primera consulta.
_database_url = os.getenv("DATABASE_URL")
DATABASES = (
    {"default": dj_database_url.parse(_database_url, conn_max_age=0)} if _database_url else {}
)
