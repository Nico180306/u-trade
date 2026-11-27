"""Configuración común a todos los entornos de U-Trade (v1.2 FINAL).

Este módulo NO carga `backend/.env`: esa carga vive exclusivamente en `local.py`.
"""

import os
from pathlib import Path

import cloudinary

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_list(name: str, default: str = "") -> list[str]:
    """Lee una variable de entorno separada por comas y devuelve una lista limpia."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("true", "1", "yes")


SECRET_KEY = os.getenv("SECRET_KEY", "")
DEBUG = False
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "cloudinary",
    "apps.core",
    "apps.accounts",
    "apps.sellers",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.core.middleware.InternalProxyMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
        "DIRS": [],
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

# Cada entorno define DATABASES (local, test, production). Sin base de datos de respaldo.
DATABASES: dict = {}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Tiempo: UTC estricto (Regla 5). El formateo a America/Guayaquil es del frontend. ---
LANGUAGE_CODE = "es-ec"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Parámetros globales congelados v1.2 ---
CANCELLATION_CUTOFF_MINUTES = 30
RELEASE_LOCK_MINUTES = 30
RECONCILIATION_WINDOW_HOURS = 2
STRIKE_THRESHOLD = 2
STRIKE_WINDOW_DAYS = 30
SUSPENSION_DAYS = 7
DISPUTE_WINDOW_HOURS = 72
MAX_ACTIVE_RESERVATIONS_PER_BUYER = 5
REVIEW_SELLER_COOLDOWN_DAYS = 30
OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_MAX_SENDS_PER_15MIN = 3

# --- Caché compartida entre workers/instancias (throttling). Requiere `createcachetable`. ---
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
    }
}

# --- Secretos de borde ---
INTERNAL_PROXY_SECRET = os.getenv("INTERNAL_PROXY_SECRET", "")
CRON_SECRET = os.getenv("CRON_SECRET", "")

# --- Sesiones + CSRF (sin JWT) ---
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
CSRF_FAILURE_VIEW = "apps.core.views.csrf_failure"

# --- CORS & Frontend ---
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
CORS_ALLOW_CREDENTIALS = True
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")

# --- Correo (apps.core.email.EmailService) ---
# "console": send_mail -> EMAIL_BACKEND (local/test). "resend": API HTTPS de Resend (producción).
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "console").strip().lower()
# EMAIL_FROM es el nombre canónico; RESEND_FROM_EMAIL se acepta como respaldo heredado.
DEFAULT_FROM_EMAIL = (
    os.getenv("EMAIL_FROM") or os.getenv("RESEND_FROM_EMAIL") or "onboarding@resend.dev"
)

# --- OTP: HMAC-SHA256(OTP_SIGNING_SECRET, "user_id:purpose:target_email:code") ---
OTP_SIGNING_SECRET = os.getenv("OTP_SIGNING_SECRET", "")

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/minute",
        "register": "5/hour",
        "password_reset": "5/hour",
        # OTP_MAX_SENDS_PER_15MIN también por IP real (el límite por usuario vive en services).
        "otp_request": "3/15m",
        "otp_verify": "10/minute",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "U-Trade API",
    "DESCRIPTION": (
        "API REST de U-Trade v1.2. Autenticación por sesión Django + CSRF. "
        'Errores uniformes: {"code", "message", "details"}. Fechas en UTC ISO-8601.'
    ),
    "VERSION": "1.2.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "ErrorCodeEnum": "apps.core.exceptions.ErrorCode",
    },
}

# --- Cloudinary (las firmas se implementan en feature/sales-management-be) ---
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    api_key=os.getenv("CLOUDINARY_API_KEY", ""),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
    secure=True,
)

# --- Resend ---
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
