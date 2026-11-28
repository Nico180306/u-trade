"""Fixtures compartidas. Todos los tests corren sobre PostgreSQL 16 real (config.settings.test)."""

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.core.testing import USER_EMAIL, USER_PASSWORD, bootstrap_csrf, login, make_client
from apps.core.throttling import ClientIPRateThrottle


@pytest.fixture(autouse=True)
def _isolated_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    return make_client()


@pytest.fixture
def csrf_client(api_client) -> APIClient:
    return bootstrap_csrf(api_client)


@pytest.fixture
def user(db) -> User:
    return User.objects.create_user(
        email=USER_EMAIL,
        password=USER_PASSWORD,
        full_name="Ana Pérez",
        phone_number="0999999999",
    )


@pytest.fixture
def logged_client(csrf_client, user) -> APIClient:
    response = login(csrf_client)
    assert response.status_code == 200, response.content
    return csrf_client


@pytest.fixture
def relaxed_otp_throttle(monkeypatch):
    """Sube las tasas por IP de OTP para probar las reglas por (usuario, propósito) de services
    sin que el throttle por IP (3/15m) responda antes con THROTTLED."""
    monkeypatch.setitem(ClientIPRateThrottle.THROTTLE_RATES, "otp_request", "100/minute")
    monkeypatch.setitem(ClientIPRateThrottle.THROTTLE_RATES, "otp_verify", "100/minute")
