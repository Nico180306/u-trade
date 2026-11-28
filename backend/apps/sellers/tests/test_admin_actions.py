"""Acciones del Django Admin: siempre pasan por sellers.services."""

import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.core.testing import USER_PASSWORD
from apps.sellers.models import SellerApplication, SellerApplicationStatus, SellerProfile

pytestmark = pytest.mark.django_db

CHANGELIST = "admin:sellers_sellerapplication_changelist"


@pytest.fixture
def admin_client(client, db):
    admin = User.objects.create_superuser(email="root@example.com", password=USER_PASSWORD)
    client.force_login(admin)
    client.admin_user = admin
    return client


def run_action(admin_client, action: str, ids, **extra):
    return admin_client.post(
        reverse(CHANGELIST),
        {"action": action, "_selected_action": [str(i) for i in ids], **extra},
    )


def test_approve_action_uses_service(
    admin_client, pending_application, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = run_action(admin_client, "approve_applications", [pending_application.id])

    assert response.status_code == 302
    pending_application.refresh_from_db()
    assert pending_application.status == SellerApplicationStatus.APPROVED
    assert pending_application.reviewed_by == admin_client.admin_user
    assert SellerProfile.objects.filter(user=pending_application.user, is_active=True).exists()
    assert AuditLog.objects.filter(
        action="SELLER_APPLICATION_APPROVED", entity_id=pending_application.id
    ).exists()
    assert len(mail.outbox) == 1


def test_reject_action_shows_reason_form_before_rejecting(admin_client, pending_application):
    response = run_action(admin_client, "reject_applications", [pending_application.id])

    assert response.status_code == 200
    assert b"Motivo del rechazo" in response.content
    pending_application.refresh_from_db()
    assert pending_application.status == SellerApplicationStatus.PENDING


def test_reject_action_with_empty_reason_keeps_form(admin_client, pending_application):
    response = run_action(
        admin_client,
        "reject_applications",
        [pending_application.id],
        apply="1",
        rejection_reason="",
    )

    assert response.status_code == 200
    pending_application.refresh_from_db()
    assert pending_application.status == SellerApplicationStatus.PENDING


def test_reject_action_with_reason_uses_service(
    admin_client, pending_application, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = run_action(
            admin_client,
            "reject_applications",
            [pending_application.id],
            apply="1",
            rejection_reason="Falta información del producto",
        )

    assert response.status_code == 302
    pending_application.refresh_from_db()
    assert pending_application.status == SellerApplicationStatus.REJECTED
    assert pending_application.rejection_reason == "Falta información del producto"
    assert AuditLog.objects.filter(
        action="SELLER_APPLICATION_REJECTED", entity_id=pending_application.id
    ).exists()
    assert "Falta información del producto" in mail.outbox[0].body


def test_approve_action_reports_already_reviewed_without_changes(
    admin_client, pending_application, django_capture_on_commit_callbacks
):
    SellerApplication.objects.filter(pk=pending_application.pk).update(
        status=SellerApplicationStatus.REJECTED
    )

    with django_capture_on_commit_callbacks(execute=True):
        response = run_action(admin_client, "approve_applications", [pending_application.id])

    assert response.status_code == 302
    messages = [str(m) for m in response.wsgi_request._messages]
    assert any("ya fue revisada" in m for m in messages)
    assert not SellerProfile.objects.exists()
    assert mail.outbox == []


def test_admin_change_form_does_not_allow_direct_status_edit(admin_client, pending_application):
    url = reverse("admin:sellers_sellerapplication_change", args=[pending_application.id])
    response = admin_client.get(url)
    assert response.status_code == 200
    assert b'name="status"' not in response.content

    admin_client.post(url, {"status": "APPROVED"})
    pending_application.refresh_from_db()
    assert pending_application.status == SellerApplicationStatus.PENDING


def test_seller_profile_admin_is_read_only(admin_client, seller_profile):
    url = reverse("admin:sellers_sellerprofile_change", args=[seller_profile.id])
    response = admin_client.get(url)
    assert response.status_code == 200
    assert b'name="avg_rating"' not in response.content
    assert b'name="is_active"' not in response.content
    assert admin_client.get(reverse("admin:sellers_sellerprofile_changelist")).status_code == 200
