import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.core.testing import CRON_SECRET, PROXY_SECRET, assert_error

pytestmark = pytest.mark.django_db

CRON_PATH = "/api/v1/cron/sweep/"


def test_cron_with_valid_secret_runs_without_proxy_secret_or_csrf():
    client = APIClient(enforce_csrf_checks=True, HTTP_X_CRON_SECRET=CRON_SECRET)

    response = client.post(CRON_PATH)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "processed": 0}


def test_cron_without_secret_is_forbidden():
    assert_error(APIClient().post(CRON_PATH), 403, "UNAUTHORIZED")


def test_cron_with_wrong_secret_is_forbidden():
    client = APIClient(HTTP_X_CRON_SECRET="incorrecto")
    assert_error(client.post(CRON_PATH), 403, "UNAUTHORIZED")


def test_cron_does_not_accept_proxy_secret_instead_of_cron_secret():
    client = APIClient(HTTP_X_INTERNAL_PROXY_SECRET=PROXY_SECRET)
    assert_error(client.post(CRON_PATH), 403, "UNAUTHORIZED")


@override_settings(CRON_SECRET="")
def test_cron_with_empty_configured_secret_fails_closed():
    client = APIClient(HTTP_X_CRON_SECRET="")
    assert_error(client.post(CRON_PATH), 403, "UNAUTHORIZED")
