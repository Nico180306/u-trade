import re

import pytest
from django.core import mail

from apps.core.models import AuditLog
from apps.core.testing import (
    NEW_PASSWORD,
    USER_EMAIL,
    assert_error,
    bootstrap_csrf,
    login,
    make_client,
)

pytestmark = pytest.mark.django_db

REQUEST = "/api/v1/auth/password-reset/request/"
CONFIRM = "/api/v1/auth/password-reset/confirm/"
LINK_RE = re.compile(
    r"http://testserver-frontend/reset-password\?uid=(?P<uid>[^&\s]+)&token=(?P<token>\S+)"
)


def request_reset_link(client, django_capture_on_commit_callbacks) -> dict:
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(REQUEST, {"email": USER_EMAIL}, format="json")
    assert response.status_code == 204
    match = LINK_RE.search(mail.outbox[-1].body)
    assert match, mail.outbox[-1].body
    return match.groupdict()


def test_request_for_unknown_email_is_neutral_and_sends_nothing(
    csrf_client, user, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        response = csrf_client.post(REQUEST, {"email": "nadie@example.com"}, format="json")

    assert response.status_code == 204
    assert response.content == b""
    assert callbacks == []
    assert mail.outbox == []


def test_request_for_existing_email_has_same_response_and_mails_only_after_commit(
    csrf_client, user, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        response = csrf_client.post(REQUEST, {"email": USER_EMAIL.upper()}, format="json")

    assert response.status_code == 204
    assert response.content == b""
    assert len(callbacks) == 1
    assert mail.outbox == []  # nada sale antes del commit

    callbacks[0]()
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [USER_EMAIL]
    assert LINK_RE.search(mail.outbox[0].body)


def test_confirm_sets_new_password_and_invalidates_existing_sessions(
    csrf_client, user, django_capture_on_commit_callbacks
):
    logged_elsewhere = bootstrap_csrf(make_client())
    assert login(logged_elsewhere).status_code == 200

    link = request_reset_link(csrf_client, django_capture_on_commit_callbacks)
    response = csrf_client.post(
        CONFIRM,
        {"uid": link["uid"], "token": link["token"], "new_password": NEW_PASSWORD},
        format="json",
    )

    assert response.status_code == 204, response.content
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
    assert AuditLog.objects.filter(action="PASSWORD_RESET", entity_id=user.id).exists()
    assert_error(logged_elsewhere.get("/api/v1/auth/me/"), 403, "NOT_AUTHENTICATED")


def test_confirm_token_cannot_be_reused(csrf_client, user, django_capture_on_commit_callbacks):
    link = request_reset_link(csrf_client, django_capture_on_commit_callbacks)
    data = {"uid": link["uid"], "token": link["token"], "new_password": NEW_PASSWORD}
    assert csrf_client.post(CONFIRM, data, format="json").status_code == 204

    data["new_password"] = "Tercera-Clave-2026!"
    assert_error(csrf_client.post(CONFIRM, data, format="json"), 400, "INVALID_RESET_TOKEN")


@pytest.mark.parametrize(
    "uid,token",
    [("bm8tZXhpc3Rl", "token-falso"), ("!!!", "token-falso"), ("", "")],
)
def test_confirm_with_invalid_uid_or_token(csrf_client, user, uid, token):
    response = csrf_client.post(
        CONFIRM,
        {"uid": uid or "x", "token": token or "y", "new_password": NEW_PASSWORD},
        format="json",
    )
    assert_error(response, 400, "INVALID_RESET_TOKEN")


def test_confirm_with_valid_token_but_weak_password(
    csrf_client, user, django_capture_on_commit_callbacks
):
    link = request_reset_link(csrf_client, django_capture_on_commit_callbacks)
    response = csrf_client.post(
        CONFIRM,
        {"uid": link["uid"], "token": link["token"], "new_password": "123"},
        format="json",
    )

    body = assert_error(response, 400, "VALIDATION_ERROR")
    assert body["details"]["password"]
