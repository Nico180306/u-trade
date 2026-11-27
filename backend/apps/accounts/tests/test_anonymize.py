import pytest

from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.core.testing import (
    USER_EMAIL,
    USER_PASSWORD,
    assert_error,
    bootstrap_csrf,
    login,
    make_client,
)

pytestmark = pytest.mark.django_db

DELETE = "/api/v1/auth/me/delete/"
ME = "/api/v1/auth/me/"


def snapshot(user: User) -> tuple:
    user.refresh_from_db()
    return (user.email, user.full_name, user.phone_number, user.is_active, user.password)


def test_delete_with_wrong_current_password_returns_400_and_does_not_anonymize(logged_client, user):
    before = snapshot(user)

    response = logged_client.post(DELETE, {"current_password": "incorrecta"}, format="json")

    assert_error(response, 400, "INVALID_PASSWORD")
    assert snapshot(user) == before
    assert not AuditLog.objects.filter(action="USER_ANONYMIZED").exists()
    assert logged_client.get(ME).status_code == 200


def test_delete_without_current_password_is_a_validation_error(logged_client, user):
    before = snapshot(user)

    body = assert_error(logged_client.post(DELETE, {}, format="json"), 400, "VALIDATION_ERROR")

    assert "current_password" in body["details"]
    assert snapshot(user) == before


def test_delete_without_csrf_token_is_rejected(logged_client, user):
    before = snapshot(user)
    del logged_client.defaults["HTTP_X_CSRFTOKEN"]

    response = logged_client.post(DELETE, {"current_password": USER_PASSWORD}, format="json")

    assert_error(response, 403, "CSRF_FAILED")
    assert snapshot(user) == before


def test_delete_requires_authentication(csrf_client):
    response = csrf_client.post(DELETE, {"current_password": USER_PASSWORD}, format="json")
    assert_error(response, 403, "NOT_AUTHENTICATED")


def test_delete_anonymizes_account_logs_audit_and_kills_all_sessions(logged_client, user):
    user.uisek_email = "ana@uisek.edu.ec"
    user.save(update_fields=["uisek_email"])
    other_session = bootstrap_csrf(make_client())
    assert login(other_session).status_code == 200

    response = logged_client.post(DELETE, {"current_password": USER_PASSWORD}, format="json")

    assert response.status_code == 204, response.content
    user.refresh_from_db()
    assert user.email == f"deleted_{user.id.hex}@anon.utrade.local"
    assert user.full_name == "Usuario eliminado"
    assert user.phone_number == ""
    assert user.uisek_email is None
    assert user.uisek_email_verified_at is None
    assert user.is_active is False
    assert user.has_usable_password() is False

    audit = AuditLog.objects.get(action="USER_ANONYMIZED", entity_id=user.id)
    assert audit.metadata == {}

    # la sesión actual y cualquier otra quedan invalidadas
    assert_error(logged_client.get(ME), 403, "NOT_AUTHENTICATED")
    assert_error(other_session.get(ME), 403, "NOT_AUTHENTICATED")

    # no se puede volver a entrar con las credenciales anteriores
    fresh = bootstrap_csrf(make_client())
    assert_error(login(fresh, email=USER_EMAIL), 400, "INVALID_CREDENTIALS")
