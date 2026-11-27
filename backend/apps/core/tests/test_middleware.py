import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.core.testing import PROXY_SECRET, assert_error

pytestmark = pytest.mark.django_db

FORBIDDEN_PROXY_BODY = {
    "code": "FORBIDDEN_PROXY",
    "message": "Acceso directo no permitido.",
    "details": {},
}


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/v1/auth/csrf/"),
        ("get", "/api/v1/auth/me/"),
        ("post", "/api/v1/auth/login/"),
        ("post", "/api/v1/auth/register/"),
        ("get", "/api/v1/ruta-inexistente/"),
    ],
)
def test_api_v1_without_proxy_secret_is_forbidden(method, path):
    response = getattr(APIClient(), method)(path)

    assert response.status_code == 403
    assert response.json() == FORBIDDEN_PROXY_BODY


def test_api_v1_with_wrong_proxy_secret_is_forbidden():
    client = APIClient(HTTP_X_INTERNAL_PROXY_SECRET="otro-secreto")
    assert_error(client.get("/api/v1/auth/csrf/"), 403, "FORBIDDEN_PROXY")


def test_api_v1_with_valid_proxy_secret_passes():
    client = APIClient(HTTP_X_INTERNAL_PROXY_SECRET=PROXY_SECRET)
    assert client.get("/api/v1/auth/csrf/").status_code == 204


@override_settings(INTERNAL_PROXY_SECRET="")
def test_empty_configured_secret_fails_closed():
    client = APIClient(HTTP_X_INTERNAL_PROXY_SECRET="")
    assert_error(client.get("/api/v1/auth/csrf/"), 403, "FORBIDDEN_PROXY")


def test_admin_is_exempt_from_proxy_secret():
    response = APIClient().get("/admin/login/")
    assert response.status_code == 200
