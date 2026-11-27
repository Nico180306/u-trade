import pytest
from rest_framework import status
from rest_framework.exceptions import Throttled

from apps.core.exceptions import DomainError, custom_exception_handler
from apps.core.testing import assert_error

pytestmark = pytest.mark.django_db


def test_domain_error_is_rendered_in_uniform_format():
    exc = DomainError(
        "INSUFFICIENT_STOCK",
        "Sin stock suficiente.",
        status_code=status.HTTP_409_CONFLICT,
        details={"available": 1},
    )

    response = custom_exception_handler(exc, {})

    assert response.status_code == 409
    assert response.data == {
        "code": "INSUFFICIENT_STOCK",
        "message": "Sin stock suficiente.",
        "details": {"available": 1},
    }


def test_unhandled_exception_becomes_internal_error():
    response = custom_exception_handler(RuntimeError("boom"), {})

    assert response.status_code == 500
    assert response.data["code"] == "INTERNAL_ERROR"
    assert response.data["details"] == {}


def test_throttled_exposes_wait_seconds():
    response = custom_exception_handler(Throttled(wait=42), {})

    assert response.status_code == 429
    assert response.data["code"] == "THROTTLED"
    assert response.data["details"] == {"wait_seconds": 42}


def test_validation_error_lists_fields_in_details(csrf_client):
    response = csrf_client.post("/api/v1/auth/register/", {}, format="json")

    body = assert_error(response, 400, "VALIDATION_ERROR")
    assert {"email", "password", "accept_terms", "accept_privacy"} <= set(body["details"])


def test_not_authenticated_uses_uniform_format(api_client):
    assert_error(api_client.get("/api/v1/auth/me/"), 403, "NOT_AUTHENTICATED")


def test_method_not_allowed_uses_uniform_format(csrf_client):
    assert_error(csrf_client.get("/api/v1/auth/login/"), 405, "METHOD_NOT_ALLOWED")


def test_malformed_json_uses_uniform_format(csrf_client):
    response = csrf_client.post(
        "/api/v1/auth/login/", data="{no-es-json", content_type="application/json"
    )
    assert_error(response, 400, "PARSE_ERROR")
