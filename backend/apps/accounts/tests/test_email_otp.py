"""OTP de comprador (BUYER_EMAIL): envío, verificación, expiración, bloqueo, límites y atajo
@uisek.edu.ec. PostgreSQL 16 real."""

from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts.models import EmailVerificationOTP, OTPPurpose, User
from apps.accounts.services import otp_code_hash
from apps.core.models import AuditLog
from apps.core.testing import (
    USER_EMAIL,
    USER_PASSWORD,
    assert_error,
    bootstrap_csrf,
    last_otp_code,
    login,
    make_client,
    wrong_code,
)

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("relaxed_otp_throttle")]

REQUEST = "/api/v1/auth/email-otp/request/"
VERIFY = "/api/v1/auth/email-otp/verify/"


def request_otp(client, capture) -> str:
    with capture(execute=True):
        response = client.post(REQUEST)
    assert response.status_code == 200, response.content
    return last_otp_code()


def verify(client, code: str):
    return client.post(VERIFY, {"code": code}, format="json")


def logged_client_for(email: str, password: str = USER_PASSWORD, ip: str = "203.0.113.20"):
    client = bootstrap_csrf(make_client(client_ip=ip))
    assert login(client, email=email, password=password).status_code == 200
    return client


# --- Envío ------------------------------------------------------------------------------------


def test_request_creates_hashed_otp_and_emails_only_after_commit(
    logged_client, user, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        response = logged_client.post(REQUEST)

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["purpose"] == "BUYER_EMAIL"
    assert body["target_email"] == USER_EMAIL
    assert body["expires_at"].endswith("Z")
    assert mail.outbox == []  # nada sale antes del commit
    assert len(callbacks) == 1

    callbacks[0]()
    code = last_otp_code(USER_EMAIL)
    otp = EmailVerificationOTP.objects.get(user=user)
    assert otp.purpose == OTPPurpose.BUYER_EMAIL
    assert otp.target_email == USER_EMAIL
    assert len(otp.code_hash) == 64 and code not in otp.code_hash
    assert otp.code_hash == otp_code_hash(
        user_id=user.id, purpose="BUYER_EMAIL", target_email=USER_EMAIL, code=code
    )
    ttl = otp.expires_at - otp.created_at
    assert timedelta(minutes=9, seconds=59) < ttl <= timedelta(minutes=10, seconds=1)
    assert otp.attempts_count == 0 and otp.consumed_at is None
    assert code not in mail.outbox[0].subject


def test_request_requires_authentication(csrf_client):
    assert_error(csrf_client.post(REQUEST), 403, "NOT_AUTHENTICATED")


def test_request_requires_csrf(logged_client):
    del logged_client.defaults["HTTP_X_CSRFTOKEN"]
    assert_error(logged_client.post(REQUEST), 403, "CSRF_FAILED")
    assert not EmailVerificationOTP.objects.exists()


def test_new_request_invalidates_previous_active_otp(
    logged_client, user, django_capture_on_commit_callbacks
):
    first_code = request_otp(logged_client, django_capture_on_commit_callbacks)
    second_code = request_otp(logged_client, django_capture_on_commit_callbacks)

    first, second = EmailVerificationOTP.objects.filter(user=user).order_by("created_at")
    assert first.consumed_at is not None
    assert second.consumed_at is None

    if first_code != second_code:
        assert_error(verify(logged_client, first_code), 400, "OTP_INVALID")
    assert verify(logged_client, second_code).status_code == 200


def test_fourth_send_within_15_minutes_is_rate_limited(
    logged_client, user, django_capture_on_commit_callbacks
):
    for i in range(3):
        logged_client.defaults["HTTP_X_CLIENT_IP"] = f"198.51.100.{i}"
        request_otp(logged_client, django_capture_on_commit_callbacks)

    logged_client.defaults["HTTP_X_CLIENT_IP"] = "198.51.100.200"
    body = assert_error(logged_client.post(REQUEST), 429, "OTP_RATE_LIMITED")

    assert 0 < body["details"]["retry_after_seconds"] <= 15 * 60
    assert EmailVerificationOTP.objects.filter(user=user).count() == 3
    assert len(mail.outbox) == 3


def test_sends_older_than_15_minutes_do_not_count(
    logged_client, user, django_capture_on_commit_callbacks
):
    for _ in range(3):
        request_otp(logged_client, django_capture_on_commit_callbacks)
    EmailVerificationOTP.objects.filter(user=user).update(
        created_at=timezone.now() - timedelta(minutes=16)
    )

    request_otp(logged_client, django_capture_on_commit_callbacks)
    assert EmailVerificationOTP.objects.filter(user=user).count() == 4


def test_request_when_already_verified(logged_client, user):
    User.objects.filter(pk=user.pk).update(email_verified_at=timezone.now())

    assert_error(logged_client.post(REQUEST), 400, "EMAIL_ALREADY_VERIFIED")
    assert not EmailVerificationOTP.objects.exists()


# --- Verificación -----------------------------------------------------------------------------


def test_verify_correct_code_marks_email_verified_and_audits(
    logged_client, user, django_capture_on_commit_callbacks
):
    code = request_otp(logged_client, django_capture_on_commit_callbacks)

    response = verify(logged_client, code)

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["is_email_verified"] is True
    assert body["email_verified_at"] is not None
    assert body["is_uisek_verified"] is False  # correo externo: sin atajo
    user.refresh_from_db()
    assert user.email_verified_at is not None
    assert user.uisek_email is None
    assert EmailVerificationOTP.objects.get(user=user).consumed_at is not None
    audit = AuditLog.objects.get(action="EMAIL_VERIFIED", entity_id=user.id)
    assert audit.metadata == {"purpose": "BUYER_EMAIL", "uisek_shortcut": False}

    # El código ya consumido no sirve otra vez.
    assert_error(verify(logged_client, code), 400, "OTP_EXPIRED_OR_INVALID")


def test_verify_without_any_otp(logged_client):
    assert_error(verify(logged_client, "123456"), 400, "OTP_EXPIRED_OR_INVALID")


def test_verify_expired_otp(logged_client, user, django_capture_on_commit_callbacks):
    code = request_otp(logged_client, django_capture_on_commit_callbacks)
    EmailVerificationOTP.objects.filter(user=user).update(expires_at=timezone.now())

    assert_error(verify(logged_client, code), 400, "OTP_EXPIRED_OR_INVALID")
    user.refresh_from_db()
    assert user.email_verified_at is None


@pytest.mark.parametrize("code", ["12345", "1234567", "abcdef", "", "12 456"])
def test_verify_rejects_malformed_codes(logged_client, code):
    body = assert_error(verify(logged_client, code), 400, "VALIDATION_ERROR")
    assert "code" in body["details"]


def test_wrong_codes_count_attempts_and_fifth_failure_locks(
    logged_client, user, django_capture_on_commit_callbacks
):
    code = request_otp(logged_client, django_capture_on_commit_callbacks)
    bad = wrong_code(code)

    for remaining in (4, 3, 2, 1):
        body = assert_error(verify(logged_client, bad), 400, "OTP_INVALID")
        assert body["details"] == {"attempts_remaining": remaining}

    assert_error(verify(logged_client, bad), 400, "OTP_LOCKED")

    otp = EmailVerificationOTP.objects.get(user=user)
    assert otp.attempts_count == 5
    assert otp.consumed_at is not None  # el intento fallido persiste pese al error HTTP
    assert AuditLog.objects.filter(action="OTP_LOCKED", entity_id=otp.id).exists()

    # Bloqueado: ni siquiera el código correcto funciona; hay que pedir uno nuevo.
    assert_error(verify(logged_client, code), 400, "OTP_EXPIRED_OR_INVALID")
    user.refresh_from_db()
    assert user.email_verified_at is None

    new_code = request_otp(logged_client, django_capture_on_commit_callbacks)
    assert verify(logged_client, new_code).status_code == 200


def test_otp_of_one_user_does_not_verify_another(
    logged_client, user, django_capture_on_commit_callbacks
):
    code = request_otp(logged_client, django_capture_on_commit_callbacks)
    User.objects.create_user(email="otro@example.com", password=USER_PASSWORD)
    other = logged_client_for("otro@example.com")

    assert_error(verify(other, code), 400, "OTP_EXPIRED_OR_INVALID")


def test_buyer_and_uisek_otps_are_independent(
    logged_client, user, django_capture_on_commit_callbacks
):
    code = request_otp(logged_client, django_capture_on_commit_callbacks)
    with django_capture_on_commit_callbacks(execute=True):
        response = logged_client.post(
            "/api/v1/sellers/uisek-otp/request/",
            {"uisek_email": "ana@uisek.edu.ec"},
            format="json",
        )
    assert response.status_code == 200, response.content

    buyer_otp = EmailVerificationOTP.objects.get(user=user, purpose="BUYER_EMAIL")
    assert buyer_otp.consumed_at is None  # pedir el OTP UISEK no invalida el de comprador
    assert verify(logged_client, code).status_code == 200


# --- Atajo @uisek.edu.ec ----------------------------------------------------------------------


def test_uisek_registered_user_gets_uisek_verified_with_buyer_otp(
    django_capture_on_commit_callbacks,
):
    student = User.objects.create_user(email="Estudiante@UISEK.edu.ec", password=USER_PASSWORD)
    client = logged_client_for("estudiante@uisek.edu.ec")
    code = request_otp(client, django_capture_on_commit_callbacks)

    body = verify(client, code).json()

    assert body["is_email_verified"] is True
    assert body["is_uisek_verified"] is True
    assert body["uisek_email"] == "estudiante@uisek.edu.ec"
    student.refresh_from_db()
    assert student.email_verified_at == student.uisek_email_verified_at
    audit = AuditLog.objects.get(action="EMAIL_VERIFIED", entity_id=student.id)
    assert audit.metadata == {"purpose": "BUYER_EMAIL", "uisek_shortcut": True}


def test_uisek_shortcut_skipped_when_address_already_claimed(
    django_capture_on_commit_callbacks,
):
    User.objects.create_user(
        email="dueno@example.com",
        password=USER_PASSWORD,
        uisek_email="estudiante@uisek.edu.ec",
        uisek_email_verified_at=timezone.now(),
    )
    student = User.objects.create_user(email="estudiante@uisek.edu.ec", password=USER_PASSWORD)
    client = logged_client_for("estudiante@uisek.edu.ec")
    code = request_otp(client, django_capture_on_commit_callbacks)

    body = verify(client, code).json()

    assert body["is_email_verified"] is True
    assert body["is_uisek_verified"] is False
    student.refresh_from_db()
    assert student.uisek_email is None


def test_lookalike_uisek_domain_does_not_trigger_shortcut(django_capture_on_commit_callbacks):
    User.objects.create_user(email="ana@uisek.edu.ec.evil.com", password=USER_PASSWORD)
    client = logged_client_for("ana@uisek.edu.ec.evil.com")
    code = request_otp(client, django_capture_on_commit_callbacks)

    body = verify(client, code).json()

    assert body["is_email_verified"] is True
    assert body["is_uisek_verified"] is False


# --- Throttle por IP real ---------------------------------------------------------------------


def test_otp_request_is_throttled_per_client_ip(monkeypatch, user):
    from apps.core.throttling import ClientIPRateThrottle

    monkeypatch.setitem(ClientIPRateThrottle.THROTTLE_RATES, "otp_request", "3/15m")
    others = [
        User.objects.create_user(email=f"u{i}@example.com", password=USER_PASSWORD)
        for i in range(4)
    ]
    shared_ip = "192.0.2.50"  # p. ej. NAT del campus
    clients = [logged_client_for(u.email, ip=shared_ip) for u in others]

    for client in clients[:3]:
        assert client.post(REQUEST).status_code == 200

    body = assert_error(clients[3].post(REQUEST), 429, "THROTTLED")
    assert body["details"]["wait_seconds"] > 0
    assert logged_client_for(USER_EMAIL, ip="192.0.2.51").post(REQUEST).status_code == 200
