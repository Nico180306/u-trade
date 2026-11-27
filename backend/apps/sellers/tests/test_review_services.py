"""approve/reject_seller_application vía services: estados, SellerProfile, AuditLog y correo
solo tras commit."""

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts.models import User
from apps.core.exceptions import DomainError
from apps.core.models import AuditLog
from apps.core.testing import USER_EMAIL
from apps.sellers import services
from apps.sellers.models import SellerApplication, SellerApplicationStatus, SellerProfile

pytestmark = pytest.mark.django_db


def test_approve_creates_profile_audits_and_emails_after_commit(
    pending_application, staff_user, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        profile = services.approve_seller_application(pending_application.id, staff_user)

    assert mail.outbox == []  # nada sale antes del commit
    pending_application.refresh_from_db()
    assert pending_application.status == SellerApplicationStatus.APPROVED
    assert pending_application.reviewed_by == staff_user
    assert pending_application.reviewed_at is not None
    assert profile.user_id == pending_application.user_id
    assert profile.is_active is True
    assert profile.venture_name == pending_application.venture_name
    assert profile.contact_phone == pending_application.contact_phone
    assert str(profile.avg_rating) == "0.00" and profile.reviews_count == 0
    audit = AuditLog.objects.get(
        action="SELLER_APPLICATION_APPROVED", entity_id=pending_application.id
    )
    assert audit.actor == staff_user
    assert audit.metadata == {"seller_profile_id": str(profile.id)}

    assert len(callbacks) == 1
    callbacks[0]()
    assert mail.outbox[0].to == [USER_EMAIL]
    assert "aprobada" in mail.outbox[0].subject


def test_approve_reactivates_existing_inactive_profile(
    pending_application, staff_user, django_capture_on_commit_callbacks
):
    old = SellerProfile.objects.create(
        user=pending_application.user,
        venture_name="Viejo",
        description="Viejo",
        contact_phone="0990000000",
        is_active=False,
        reviews_count=7,
    )

    with django_capture_on_commit_callbacks(execute=True):
        profile = services.approve_seller_application(pending_application.id, staff_user)

    assert profile.id == old.id
    profile.refresh_from_db()
    assert profile.is_active is True
    assert profile.venture_name == pending_application.venture_name
    assert profile.reviews_count == 7  # métricas históricas intactas
    assert SellerProfile.objects.count() == 1


def test_reject_sets_reason_audits_and_emails_after_commit(
    pending_application, staff_user, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        services.reject_seller_application(pending_application.id, staff_user, "  Falta el logo  ")

    assert mail.outbox == []
    pending_application.refresh_from_db()
    assert pending_application.status == SellerApplicationStatus.REJECTED
    assert pending_application.rejection_reason == "Falta el logo"
    assert pending_application.reviewed_by == staff_user
    assert not SellerProfile.objects.exists()
    assert AuditLog.objects.filter(
        action="SELLER_APPLICATION_REJECTED", entity_id=pending_application.id
    ).exists()

    callbacks[0]()
    assert "Falta el logo" in mail.outbox[0].body


@pytest.mark.parametrize("reason", ["", "   ", None])
def test_reject_requires_reason(pending_application, staff_user, reason):
    with pytest.raises(DomainError) as exc:
        services.reject_seller_application(pending_application.id, staff_user, reason)

    assert exc.value.code == "REJECTION_REASON_REQUIRED"
    pending_application.refresh_from_db()
    assert pending_application.status == SellerApplicationStatus.PENDING


@pytest.mark.parametrize("final_status", ["APPROVED", "REJECTED"])
def test_reviewed_application_cannot_be_reviewed_again(
    pending_application, staff_user, final_status, django_capture_on_commit_callbacks
):
    SellerApplication.objects.filter(pk=pending_application.pk).update(status=final_status)

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        with pytest.raises(DomainError) as approve_exc:
            services.approve_seller_application(pending_application.id, staff_user)
        with pytest.raises(DomainError) as reject_exc:
            services.reject_seller_application(pending_application.id, staff_user, "x")

    assert approve_exc.value.code == reject_exc.value.code == "SELLER_APPLICATION_NOT_PENDING"
    assert approve_exc.value.status_code == 409
    assert callbacks == [] and mail.outbox == []
    assert not SellerProfile.objects.exists()


def test_non_staff_cannot_review(pending_application, user):
    with pytest.raises(DomainError) as exc:
        services.approve_seller_application(pending_application.id, user)
    assert exc.value.code == "PERMISSION_DENIED"


def test_approve_fails_if_applicant_lost_uisek_verification(pending_application, staff_user):
    User.objects.filter(pk=pending_application.user_id).update(
        uisek_email=None, uisek_email_verified_at=None
    )

    with pytest.raises(DomainError) as exc:
        services.approve_seller_application(pending_application.id, staff_user)

    assert exc.value.code == "UISEK_NOT_VERIFIED"
    pending_application.refresh_from_db()
    assert pending_application.status == SellerApplicationStatus.PENDING
    assert not SellerProfile.objects.exists()


def test_approve_unknown_application(staff_user):
    import uuid

    with pytest.raises(DomainError) as exc:
        services.approve_seller_application(uuid.uuid4(), staff_user)
    assert exc.value.code == "NOT_FOUND"


def test_approved_seller_shows_in_me(logged_client, pending_application, staff_user):
    profile = services.approve_seller_application(pending_application.id, staff_user)

    body = logged_client.get("/api/v1/auth/me/").json()

    assert body["is_seller"] is True
    assert body["seller_profile_id"] == str(profile.id)

    SellerProfile.objects.filter(pk=profile.pk).update(is_active=False)
    body = logged_client.get("/api/v1/auth/me/").json()
    assert body["is_seller"] is False and body["seller_profile_id"] is None


def test_reviewed_at_is_utc(pending_application, staff_user):
    services.approve_seller_application(pending_application.id, staff_user)
    pending_application.refresh_from_db()
    assert pending_application.reviewed_at.utcoffset() == timezone.timedelta(0)
