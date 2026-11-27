import pytest

from apps.core.testing import assert_error, bootstrap_csrf, login, make_client
from apps.core.throttling import ClientIPRateThrottle

pytestmark = pytest.mark.django_db


@pytest.fixture
def auth_limit_3(monkeypatch):
    monkeypatch.setitem(ClientIPRateThrottle.THROTTLE_RATES, "auth", "3/minute")


def test_login_is_throttled_per_client_ip_after_limit(auth_limit_3, user):
    attacker = bootstrap_csrf(make_client(client_ip="198.51.100.7"))

    for _ in range(3):
        assert_error(login(attacker, password="incorrecta"), 400, "INVALID_CREDENTIALS")

    body = assert_error(login(attacker, password="incorrecta"), 429, "THROTTLED")
    assert body["details"]["wait_seconds"] > 0

    # Otra IP real conserva su propio cupo.
    legit = bootstrap_csrf(make_client(client_ip="198.51.100.8"))
    assert login(legit).status_code == 200


def test_requests_without_client_ip_share_a_single_bucket(auth_limit_3, user):
    first = bootstrap_csrf(make_client(client_ip=None))
    second = bootstrap_csrf(make_client(client_ip=None))

    for _ in range(3):
        login(first, password="incorrecta")

    assert_error(login(second, password="incorrecta"), 429, "THROTTLED")


def test_throttle_ignores_x_forwarded_for(auth_limit_3, user):
    client = bootstrap_csrf(make_client(client_ip="198.51.100.9"))

    for i in range(3):
        client.defaults["HTTP_X_FORWARDED_FOR"] = f"10.0.0.{i}"
        login(client, password="incorrecta")

    client.defaults["HTTP_X_FORWARDED_FOR"] = "10.0.0.99"
    assert_error(login(client, password="incorrecta"), 429, "THROTTLED")
