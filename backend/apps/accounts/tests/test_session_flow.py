import pytest

from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.core.testing import (
    NEW_PASSWORD,
    USER_EMAIL,
    USER_PASSWORD,
    assert_error,
    bootstrap_csrf,
    login,
    make_client,
)

pytestmark = pytest.mark.django_db

ME = "/api/v1/auth/me/"


def test_full_session_cycle_csrf_login_me_patch_password_change_logout(csrf_client, user):
    # login (case-insensitive) crea la sesión
    response = login(csrf_client, email=USER_EMAIL.upper())
    assert response.status_code == 200, response.content
    assert response.json()["id"] == str(user.id)
    assert "sessionid" in csrf_client.cookies

    # GET /me/
    me = csrf_client.get(ME)
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == USER_EMAIL
    assert body["is_seller"] is False
    assert body["seller_profile_id"] is None
    assert set(body) == {
        "id",
        "email",
        "full_name",
        "phone_number",
        "email_verified_at",
        "uisek_email",
        "uisek_email_verified_at",
        "is_email_verified",
        "is_uisek_verified",
        "is_seller",
        "seller_profile_id",
        "is_staff",
        "created_at",
    }

    # PATCH /me/ solo cambia full_name y phone_number (email se ignora)
    patched = csrf_client.patch(
        ME,
        {"full_name": "Ana María", "phone_number": "0977777777", "email": "otro@example.com"},
        format="json",
    )
    assert patched.status_code == 200, patched.content
    assert patched.json()["full_name"] == "Ana María"
    user.refresh_from_db()
    assert user.full_name == "Ana María"
    assert user.phone_number == "0977777777"
    assert user.email == USER_EMAIL

    # password-change mantiene la sesión actual
    changed = csrf_client.post(
        "/api/v1/auth/password-change/",
        {"current_password": USER_PASSWORD, "new_password": NEW_PASSWORD},
        format="json",
    )
    assert changed.status_code == 204, changed.content
    assert csrf_client.get(ME).status_code == 200
    assert AuditLog.objects.filter(action="PASSWORD_CHANGED", entity_id=user.id).exists()

    # logout
    assert csrf_client.post("/api/v1/auth/logout/").status_code == 204
    assert_error(csrf_client.get(ME), 403, "NOT_AUTHENTICATED")

    # la contraseña anterior ya no sirve, la nueva sí
    other = bootstrap_csrf(make_client())
    assert_error(login(other, password=USER_PASSWORD), 400, "INVALID_CREDENTIALS")
    assert login(other, password=NEW_PASSWORD).status_code == 200


def test_password_change_invalidates_other_sessions(user):
    first = bootstrap_csrf(make_client())
    second = bootstrap_csrf(make_client())
    assert login(first).status_code == 200
    assert login(second).status_code == 200

    response = first.post(
        "/api/v1/auth/password-change/",
        {"current_password": USER_PASSWORD, "new_password": NEW_PASSWORD},
        format="json",
    )

    assert response.status_code == 204
    assert first.get(ME).status_code == 200
    assert_error(second.get(ME), 403, "NOT_AUTHENTICATED")


def test_password_change_with_wrong_current_password(logged_client, user):
    response = logged_client.post(
        "/api/v1/auth/password-change/",
        {"current_password": "incorrecta", "new_password": NEW_PASSWORD},
        format="json",
    )

    assert_error(response, 400, "INVALID_PASSWORD")
    user.refresh_from_db()
    assert user.check_password(USER_PASSWORD)


def test_login_wrong_password_and_unknown_email_return_identical_error(csrf_client, user):
    wrong_password = login(csrf_client, password="incorrecta")
    unknown_email = login(csrf_client, email="no-existe@example.com")

    assert_error(wrong_password, 400, "INVALID_CREDENTIALS")
    assert_error(unknown_email, 400, "INVALID_CREDENTIALS")
    assert wrong_password.json() == unknown_email.json()
    assert "sessionid" not in csrf_client.cookies


def test_login_inactive_user_returns_same_generic_error(csrf_client, user):
    User.objects.filter(pk=user.pk).update(is_active=False)

    response = login(csrf_client)

    assert_error(response, 400, "INVALID_CREDENTIALS")
    assert response.json() == login(csrf_client, email="no-existe@example.com").json()


@pytest.mark.parametrize(
    "path,data",
    [
        ("/api/v1/auth/register/", {"email": "x@example.com", "password": "x"}),
        ("/api/v1/auth/login/", {"email": USER_EMAIL, "password": USER_PASSWORD}),
        ("/api/v1/auth/password-reset/request/", {"email": USER_EMAIL}),
        (
            "/api/v1/auth/password-reset/confirm/",
            {"uid": "x", "token": "y", "new_password": NEW_PASSWORD},
        ),
    ],
)
def test_anonymous_posts_without_csrf_token_are_rejected(user, path, data):
    client = make_client()
    client.get("/api/v1/auth/csrf/")  # hay cookie, pero falta la cabecera X-CSRFToken

    assert_error(client.post(path, data, format="json"), 403, "CSRF_FAILED")
    assert "sessionid" not in client.cookies


def test_authenticated_posts_without_csrf_token_are_rejected(logged_client):
    del logged_client.defaults["HTTP_X_CSRFTOKEN"]

    assert_error(logged_client.post("/api/v1/auth/logout/"), 403, "CSRF_FAILED")
    assert_error(logged_client.patch(ME, {"full_name": "Hack"}, format="json"), 403, "CSRF_FAILED")
    assert logged_client.get(ME).status_code == 200


def test_session_cookie_is_httponly_and_lax(csrf_client, user):
    login(csrf_client)

    cookie = csrf_client.cookies["sessionid"]
    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Lax"
    assert cookie["domain"] == ""
