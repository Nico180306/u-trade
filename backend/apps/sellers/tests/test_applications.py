"""SellerApplication vía API: requisitos, unicidad de PENDING y re-solicitud."""

import pytest
from django.db import IntegrityError, transaction

from apps.core.models import AuditLog
from apps.core.testing import assert_error
from apps.sellers.models import SellerApplication, SellerApplicationStatus
from apps.sellers.tests.conftest import APPLICATION_DATA

pytestmark = pytest.mark.django_db

APPLICATIONS = "/api/v1/sellers/applications/"
MINE = "/api/v1/sellers/applications/me/"


def submit(client, **overrides):
    return client.post(APPLICATIONS, {**APPLICATION_DATA, **overrides}, format="json")


def test_submit_requires_verified_uisek_email(logged_client, user):
    assert_error(submit(logged_client), 403, "UISEK_NOT_VERIFIED")
    assert not SellerApplication.objects.exists()


def test_submit_creates_pending_application_and_audit(logged_client, uisek_user):
    response = submit(logged_client)

    assert response.status_code == 201, response.content
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["instagram_handle"] == "browniesana"  # se guarda sin "@"
    assert body["rejection_reason"] == ""
    assert body["reviewed_at"] is None
    application = SellerApplication.objects.get(pk=body["id"])
    assert application.user == uisek_user
    assert AuditLog.objects.filter(
        action="SELLER_APPLICATION_SUBMITTED", entity_id=application.id
    ).exists()


def test_instagram_handle_is_optional(logged_client, uisek_user):
    data = {k: v for k, v in APPLICATION_DATA.items() if k != "instagram_handle"}
    response = logged_client.post(APPLICATIONS, data, format="json")

    assert response.status_code == 201, response.content
    assert response.json()["instagram_handle"] == ""


def test_second_pending_application_is_rejected(logged_client, pending_application):
    assert_error(submit(logged_client), 409, "SELLER_APPLICATION_ALREADY_PENDING")
    assert SellerApplication.objects.count() == 1


def test_db_constraint_enforces_single_pending_application(pending_application):
    with pytest.raises(IntegrityError), transaction.atomic():
        SellerApplication.objects.create(
            user=pending_application.user,
            venture_name="Otra",
            description="x",
            contact_phone="0990000000",
        )


def test_can_reapply_after_rejection(logged_client, pending_application):
    SellerApplication.objects.filter(pk=pending_application.pk).update(
        status=SellerApplicationStatus.REJECTED, rejection_reason="Falta información"
    )

    response = submit(logged_client, venture_name="Brownies de Ana v2")

    assert response.status_code == 201, response.content
    assert SellerApplication.objects.filter(user=pending_application.user).count() == 2


def test_active_seller_cannot_apply_again(logged_client, seller_profile):
    assert_error(submit(logged_client), 409, "ALREADY_A_SELLER")


@pytest.mark.parametrize(
    "field,value",
    [
        ("venture_name", ""),
        ("venture_name", "x" * 101),
        ("description", "x" * 1001),
        ("contact_phone", "abc"),
        ("contact_phone", "1" * 25),
        ("instagram_handle", "con espacios"),
    ],
)
def test_submit_validates_format(logged_client, uisek_user, field, value):
    body = assert_error(submit(logged_client, **{field: value}), 400, "VALIDATION_ERROR")
    assert field in body["details"]


def test_submit_requires_authentication(csrf_client, uisek_user):
    assert_error(submit(csrf_client), 403, "NOT_AUTHENTICATED")


def test_submit_requires_csrf(logged_client, uisek_user):
    del logged_client.defaults["HTTP_X_CSRFTOKEN"]
    assert_error(submit(logged_client), 403, "CSRF_FAILED")
    assert not SellerApplication.objects.exists()


def test_my_applications_are_listed_newest_first(logged_client, pending_application):
    SellerApplication.objects.filter(pk=pending_application.pk).update(
        status=SellerApplicationStatus.REJECTED, rejection_reason="Falta logo"
    )
    newest = submit(logged_client, venture_name="Segunda").json()

    body = logged_client.get(MINE).json()

    assert [a["id"] for a in body] == [newest["id"], str(pending_application.id)]
    assert body[1]["status"] == "REJECTED"
    assert body[1]["rejection_reason"] == "Falta logo"


def test_my_applications_only_shows_own(other_client, pending_application):
    assert other_client.get(MINE).json() == []


def test_my_applications_requires_authentication(api_client):
    assert_error(api_client.get(MINE), 403, "NOT_AUTHENTICATED")
