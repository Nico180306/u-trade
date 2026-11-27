from datetime import UTC, datetime, timedelta

import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("path", ["/api/v1/health/", "/api/health/"])
def test_health_ok_without_proxy_secret_returns_utc_server_time(path):
    response = APIClient().get(path)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["server_time"].endswith("Z")
    server_time = datetime.fromisoformat(body["server_time"].replace("Z", "+00:00"))
    assert server_time.utcoffset() == timedelta(0)
    assert abs(datetime.now(UTC) - server_time) < timedelta(minutes=1)


def test_health_returns_503_when_database_is_unreachable(monkeypatch):
    class BrokenConnection:
        def cursor(self):
            raise RuntimeError("db down")

    monkeypatch.setattr("apps.core.views.connection", BrokenConnection())

    response = APIClient().get("/api/v1/health/")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["database"] == "unreachable"
    assert body["server_time"].endswith("Z")


def test_health_rejects_post():
    response = APIClient().post("/api/v1/health/")
    assert response.status_code == 405
