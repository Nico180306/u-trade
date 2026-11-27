import pytest

from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.core.testing import USER_PASSWORD, assert_error, make_client

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/auth/register/"


def payload(**overrides):
    data = {
        "email": "Nuevo.Comprador@Example.com",
        "password": USER_PASSWORD,
        "full_name": "Nuevo Comprador",
        "phone_number": "0988888888",
        "accept_terms": True,
        "accept_privacy": True,
    }
    data.update(overrides)
    return data


def test_register_creates_user_opens_session_and_records_consent(csrf_client):
    response = csrf_client.post(REGISTER, payload(), format="json")

    assert response.status_code == 201, response.content
    body = response.json()
    assert body["email"] == "nuevo.comprador@example.com"
    assert body["full_name"] == "Nuevo Comprador"
    assert body["is_email_verified"] is False
    assert body["is_uisek_verified"] is False
    assert body["is_staff"] is False
    assert "password" not in body

    user = User.objects.get(email="nuevo.comprador@example.com")
    assert user.check_password(USER_PASSWORD)

    audit = AuditLog.objects.get(action="USER_REGISTERED", entity_id=user.id)
    assert audit.metadata == {"terms_accepted": True, "privacy_accepted": True}

    # La sesión quedó abierta: /me/ responde sin volver a hacer login.
    assert "sessionid" in csrf_client.cookies
    me = csrf_client.get("/api/v1/auth/me/")
    assert me.status_code == 200
    assert me.json()["id"] == str(user.id)


@pytest.mark.parametrize(
    "email", ["alguien@mailinator.com", "alguien@YOPMAIL.com", "alguien@sub.guerrillamail.com"]
)
def test_register_rejects_disposable_domains(csrf_client, email):
    response = csrf_client.post(REGISTER, payload(email=email), format="json")

    assert_error(response, 400, "DISPOSABLE_EMAIL")
    assert not User.objects.exists()


@pytest.mark.parametrize(
    "overrides",
    [
        {"accept_terms": False},
        {"accept_privacy": False},
        {"accept_terms": False, "accept_privacy": False},
    ],
)
def test_register_requires_explicit_lopdp_consent(csrf_client, overrides):
    response = csrf_client.post(REGISTER, payload(**overrides), format="json")

    assert_error(response, 400, "CONSENT_REQUIRED")
    assert not User.objects.exists()


def test_register_with_missing_consent_fields_is_a_validation_error(csrf_client):
    data = payload()
    del data["accept_terms"]
    del data["accept_privacy"]

    body = assert_error(csrf_client.post(REGISTER, data, format="json"), 400, "VALIDATION_ERROR")
    assert {"accept_terms", "accept_privacy"} <= set(body["details"])


def test_register_duplicate_email_case_insensitive_returns_409(csrf_client, user):
    response = csrf_client.post(REGISTER, payload(email=user.email.upper()), format="json")

    assert_error(response, 409, "EMAIL_ALREADY_REGISTERED")
    assert User.objects.count() == 1


def test_register_rejects_weak_password(csrf_client):
    response = csrf_client.post(REGISTER, payload(password="12345678"), format="json")

    body = assert_error(response, 400, "VALIDATION_ERROR")
    assert body["details"]["password"]
    assert not User.objects.exists()


def test_register_without_csrf_token_is_rejected():
    client = make_client()  # sin GET /csrf/ ni cabecera X-CSRFToken

    assert_error(client.post(REGISTER, payload(), format="json"), 403, "CSRF_FAILED")
    assert not User.objects.exists()
