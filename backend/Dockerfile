# syntax=docker/dockerfile:1

# ---------- Etapa 1: dependencias de producción en un venv aislado ----------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements/ requirements/
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements/prod.txt

# ---------- Etapa 2: runtime mínimo, usuario no-root ----------
FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system appuser \
    && useradd --system --gid appuser --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser . .

# collectstatic con valores ficticios inline: no quedan como ENV en la imagen ni tocan la DB.
RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY=build-only \
    INTERNAL_PROXY_SECRET=build-only \
    CRON_SECRET=build-only \
    python manage.py collectstatic --noinput \
    && chown -R appuser:appuser /app/staticfiles

USER appuser

EXPOSE 8080

# DJANGO_SETTINGS_MODULE no se fija aquí: wsgi.py usa production por defecto y manage.py usa local
# (así el servicio `backend` de docker-compose sigue ejecutando runserver con settings locales).
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 4 --timeout 60"]
