"""OTP de vendedor (UISEK_SELLER): dominio exacto, unicidad y verificación."""

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts.models import EmailVerificationOTP, User
from apps.core.models import AuditLog
from apps.core.testing import USER_PASSWORD, assert_error, last_otp_code, wrong_code

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("relaxed_otp_throttle")]

REQUEST = "/api/v1/sellers/uisek-otp/request/"
VERIFY = "/api/v1/sellers/uisek-otp/verify/"


def request_uisek(client, email: str):
    return client.post(REQUEST, {"uisek_email": email}, format="json")


def test_request_and_verify_links_uisek_email(
    logged_client, user, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = request_uisek(logged_client, "  Ana.Perez@UISEK.EDU.EC ")

    assert response.status_code == 200, response.content
    assert response.json()["purpose"] == "UISEK_SELLER"
    assert response.json()["target_email"] == "ana.perez@uisek.edu.ec"
    assert mail.outbox[-1].to == ["ana.perez@uisek.edu.ec"]  # va al correo institucional
    code = last_otp_code("ana.perez@uisek.edu.ec")

    body = logged_client.post(VERIFY, {"code": code}, format="json").json()

    assert body["is_uisek_verified"] is True
    assert body["uisek_email"] == "ana.perez@uisek.edu.ec"
    assert body["is_email_verified"] is False  # el correo personal sigue sin verificar
    user.refresh_from_db()
    assert user.uisek_email == "ana.perez@uisek.edu.ec"
    assert user.uisek_email_verified_at is not None
    assert AuditLog.objects.filter(action="UISEK_EMAIL_VERIFIED", entity_id=user.id).exists()


@pytest.mark.parametrize(
    "email",
    [
        "ana@gmail.com",
        "ana@uisek.edu.ec.evil.com",
        "ana@mail.uisek.edu.ec",
        "ana@uisek.edu",
        "ana@xuisek.edu.ec",
        "ana@uisek.edu.ec@evil.com",
    ],
)
def test_request_rejects_non_uisek_domains(logged_client, email):
    response = request_uisek(logged_client, email)

    assert response.status_code == 400
    assert response.json()["code"] in {"INVALID_UISEK_EMAIL", "VALIDATION_ERROR"}
    assert not EmailVerificationOTP.objects.exists()


def test_request_rejects_internal_spaces(logged_client):
    assert_error(request_uisek(logged_client, "ana perez@uisek.edu.ec"), 400, "VALIDATION_ERROR")
    assert not EmailVerificationOTP.objects.exists()


def test_request_conflicts_when_another_user_claimed_the_address(logged_client):
    User.objects.create_user(
        email="dueno@example.com",
        password=USER_PASSWORD,
        uisek_email="ana@uisek.edu.ec",
        uisek_email_verified_at=timezone.now(),
    )

    assert_error(
        request_uisek(logged_client, "ANA@uisek.edu.ec"), 409, "UISEK_EMAIL_ALREADY_IN_USE"
    )
    assert not EmailVerificationOTP.objects.exists()


def test_verify_conflicts_if_address_was_claimed_after_request(
    logged_client, user, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        request_uisek(logged_client, "ana@uisek.edu.ec")
    code = last_otp_code()
    User.objects.create_user(
        email="rapido@example.com",
        password=USER_PASSWORD,
        uisek_email="ana@uisek.edu.ec",
        uisek_email_verified_at=timezone.now(),
    )

    response = logged_client.post(VERIFY, {"code": code}, format="json")

    assert_error(response, 409, "UISEK_EMAIL_ALREADY_IN_USE")
    user.refresh_from_db()
    assert user.uisek_email is None and user.uisek_email_verified_at is None


def test_request_when_uisek_already_verified(logged_client, user):
    User.objects.filter(pk=user.pk).update(
        uisek_email="ana@uisek.edu.ec", uisek_email_verified_at=timezone.now()
    )

    assert_error(request_uisek(logged_client, "ana@uisek.edu.ec"), 400, "UISEK_ALREADY_VERIFIED")


def test_uisek_verify_locks_after_five_failures(
    logged_client, user, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        request_uisek(logged_client, "ana@uisek.edu.ec")
    bad = wrong_code(last_otp_code())

    for _ in range(4):
        assert_error(logged_client.post(VERIFY, {"code": bad}, format="json"), 400, "OTP_INVALID")
    assert_error(logged_client.post(VERIFY, {"code": bad}, format="json"), 400, "OTP_LOCKED")

    otp = EmailVerificationOTP.objects.get(user=user, purpose="UISEK_SELLER")
    assert otp.attempts_count == 5 and otp.consumed_at is not None


def test_uisek_otp_requires_authentication(csrf_client):
    assert_error(request_uisek(csrf_client, "ana@uisek.edu.ec"), 403, "NOT_AUTHENTICATED")
    assert_error(
        csrf_client.post(VERIFY, {"code": "123456"}, format="json"), 403, "NOT_AUTHENTICATED"
    )
