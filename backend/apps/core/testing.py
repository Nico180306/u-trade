"""Utilidades compartidas por los tests de todas las apps (no se importan en código productivo)."""

import re

from django.core import mail
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

PROXY_SECRET = "test-proxy-secret"
CRON_SECRET = "test-cron-secret"
CLIENT_IP = "203.0.113.10"
USER_EMAIL = "ana@example.com"
USER_PASSWORD = "Sup3r-Segura-2026!"
NEW_PASSWORD = "Otra-Clave-Distinta-2026!"

_OTP_RE = re.compile(r"^\s+(\d{6})\s*$", re.MULTILINE)

_WRITE_PREFIXES = ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "ALTER", "CREATE", "DROP")


def make_client(*, client_ip: str | None = CLIENT_IP, proxy: bool = True) -> APIClient:
    """APIClient que simula la Pages Function de Cloudflare y exige CSRF como un navegador."""
    client = APIClient(enforce_csrf_checks=True)
    if proxy:
        client.defaults["HTTP_X_INTERNAL_PROXY_SECRET"] = PROXY_SECRET
    if client_ip:
        client.defaults["HTTP_X_CLIENT_IP"] = client_ip
    return client


def refresh_csrf(client: APIClient) -> str:
    """Copia la cookie csrftoken vigente a X-CSRFToken (Django rota el token al iniciar sesión)."""
    token = client.cookies["csrftoken"].value
    client.defaults["HTTP_X_CSRFTOKEN"] = token
    return token


def bootstrap_csrf(client: APIClient) -> APIClient:
    response = client.get("/api/v1/auth/csrf/")
    assert response.status_code == 204, response.content
    refresh_csrf(client)
    return client


def login(client: APIClient, email: str = USER_EMAIL, password: str = USER_PASSWORD):
    response = client.post(
        "/api/v1/auth/login/", {"email": email, "password": password}, format="json"
    )
    if response.status_code == 200:
        refresh_csrf(client)
    return response


def assert_error(response, status_code: int, code: str) -> dict:
    """Verifica el formato uniforme {"code", "message", "details"} y el código esperado."""
    assert response.status_code == status_code, response.content
    body = response.json()
    assert set(body) == {"code", "message", "details"}
    assert body["code"] == code
    assert isinstance(body["message"], str) and body["message"]
    assert isinstance(body["details"], dict)
    return body


def write_statements(ctx: CaptureQueriesContext) -> list[str]:
    return [
        q["sql"]
        for q in ctx.captured_queries
        if q["sql"].lstrip().upper().startswith(_WRITE_PREFIXES)
    ]


def last_otp_code(to: str | None = None) -> str:
    """Código OTP del último correo enviado (opcionalmente filtrado por destinatario)."""
    messages = [m for m in mail.outbox if to is None or m.to == [to]]
    assert messages, "No se envió ningún correo OTP"
    match = _OTP_RE.search(messages[-1].body)
    assert match, messages[-1].body
    return match.group(1)


def wrong_code(code: str) -> str:
    return f"{(int(code) + 1) % 1_000_000:06d}"
