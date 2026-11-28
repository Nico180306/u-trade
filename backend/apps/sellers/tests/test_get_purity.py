"""Regla 2: los GET de vendedores no escriben en la base de datos."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.core.testing import make_client, write_statements

pytestmark = pytest.mark.django_db


def _assert_get_is_pure(client, path: str, expected_status: int):
    with CaptureQueriesContext(connection) as ctx:
        response = client.get(path)
    assert response.status_code == expected_status, response.content
    assert write_statements(ctx) == []


def test_public_profile_get_does_not_write(seller_profile):
    _assert_get_is_pure(make_client(), f"/api/v1/sellers/{seller_profile.id}/", 200)


def test_my_applications_get_does_not_write(logged_client, pending_application):
    _assert_get_is_pure(logged_client, "/api/v1/sellers/applications/me/", 200)


def test_me_get_with_seller_profile_does_not_write(logged_client, seller_profile):
    _assert_get_is_pure(logged_client, "/api/v1/auth/me/", 200)


def test_seller_me_get_does_not_write(logged_client, seller_profile):
    _assert_get_is_pure(logged_client, "/api/v1/sellers/me/", 200)


def test_seller_me_get_for_non_seller_does_not_write(logged_client, user):
    _assert_get_is_pure(logged_client, "/api/v1/sellers/me/", 403)
