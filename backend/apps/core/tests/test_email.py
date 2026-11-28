"""EmailService: proveedor console/locmem vs. API HTTPS de Resend (sin red real)."""

import json
import logging
import urllib.error
from unittest import mock

import pytest
from django.core import mail
from django.test import override_settings

from apps.core.email import RESEND_API_URL, RESEND_TIMEOUT_SECONDS, EmailService, mask_email

CODE = "482913"


class FakeResponse:
    def __init__(self, status: int = 200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_console_provider_uses_django_backend():
    assert EmailService.send_otp_email("ana@example.com", CODE, "BUYER_EMAIL", 10) is True

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["ana@example.com"]
    assert CODE in message.body
    assert CODE not in message.subject
    assert "10 minutos" in message.body


@override_settings(EMAIL_PROVIDER="resend", RESEND_API_KEY="")
def test_resend_without_api_key_falls_back_to_console():
    with mock.patch("urllib.request.urlopen") as urlopen:
        assert EmailService.send(to="ana@example.com", subject="s", body="b") is True
    urlopen.assert_not_called()
    assert len(mail.outbox) == 1


@override_settings(
    EMAIL_PROVIDER="resend", RESEND_API_KEY="re_test_key", DEFAULT_FROM_EMAIL="no-reply@utrade.app"
)
def test_resend_provider_posts_json_with_short_timeout():
    with mock.patch("urllib.request.urlopen", return_value=FakeResponse(200)) as urlopen:
        assert EmailService.send_seller_application_approved("ana@example.com", "Brownies")

    request = urlopen.call_args.args[0]
    assert urlopen.call_args.kwargs["timeout"] == RESEND_TIMEOUT_SECONDS == 5
    assert request.full_url == RESEND_API_URL
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer re_test_key"
    assert request.get_header("Content-type") == "application/json"
    payload = json.loads(request.data)
    assert payload["from"] == "no-reply@utrade.app"
    assert payload["to"] == ["ana@example.com"]
    assert "Brownies" in payload["text"]
    assert mail.outbox == []  # no se usó el backend de Django


@override_settings(EMAIL_PROVIDER="resend", RESEND_API_KEY="re_test_key")
@pytest.mark.parametrize(
    "error",
    [
        urllib.error.HTTPError(RESEND_API_URL, 422, "Unprocessable", {}, None),
        urllib.error.URLError("timed out"),
        TimeoutError("timed out"),
    ],
)
def test_resend_failures_are_swallowed_and_never_log_the_code(caplog, error):
    caplog.set_level(logging.INFO, logger="apps.core.email")
    with (
        mock.patch("urllib.request.urlopen", side_effect=error),
        mock.patch("apps.core.email.sentry_sdk.capture_exception") as capture,
    ):
        sent = EmailService.send_otp_email("ana@example.com", CODE, "UISEK_SELLER", 10)

    assert sent is False
    capture.assert_called_once()
    assert CODE not in caplog.text
    assert "ana@example.com" not in caplog.text
    record = caplog.records[-1]
    assert record.provider == "resend"
    assert record.to == "a***@example.com"


@override_settings(EMAIL_PROVIDER="resend", RESEND_API_KEY="re_test_key")
def test_resend_non_2xx_status_is_a_failure():
    with (
        mock.patch("urllib.request.urlopen", return_value=FakeResponse(500)),
        mock.patch("apps.core.email.sentry_sdk.capture_exception"),
    ):
        assert EmailService.send(to="ana@example.com", subject="s", body="b") is False


def test_success_log_masks_recipient_and_omits_code(caplog):
    caplog.set_level(logging.INFO, logger="apps.core.email")
    EmailService.send_otp_email("ana@example.com", CODE, "BUYER_EMAIL", 10)

    assert CODE not in caplog.text
    assert caplog.records[-1].to == "a***@example.com"
    assert caplog.records[-1].category == "otp_buyer_email"


def test_rejection_email_includes_reason():
    EmailService.send_seller_application_rejected("ana@example.com", "Brownies", "Falta logo")
    assert "Falta logo" in mail.outbox[0].body


@pytest.mark.parametrize(
    "email,masked",
    [("ana@example.com", "a***@example.com"), ("", "***"), ("sin-arroba", "***")],
)
def test_mask_email(email, masked):
    assert mask_email(email) == masked
