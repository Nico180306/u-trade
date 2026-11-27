"""Regla 2: ningún endpoint GET escribe en la base de datos."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.core.testing import make_client, write_statements

pytestmark = pytest.mark.django_db


def _assert_get_is_pure(client, path: str, expected_status: int):
    users, audits = User.objects.count(), AuditLog.objects.count()

    with CaptureQueriesContext(connection) as ctx:
        response = client.get(path)

    assert response.status_code == expected_status, response.content
    assert write_statements(ctx) == []
    assert (User.objects.count(), AuditLog.objects.count()) == (users, audits)


def test_get_me_does_not_write(logged_client):
    _assert_get_is_pure(logged_client, "/api/v1/auth/me/", 200)


def test_get_me_anonymous_does_not_write(user):
    _assert_get_is_pure(make_client(), "/api/v1/auth/me/", 403)


def test_get_csrf_does_not_write(user):
    _assert_get_is_pure(make_client(), "/api/v1/auth/csrf/", 204)


def test_get_health_does_not_write(user):
    _assert_get_is_pure(APIClient(), "/api/v1/health/", 200)
