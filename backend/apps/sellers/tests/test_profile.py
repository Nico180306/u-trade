"""Perfil público (AllowAny) y edición restringida a vendedor activo."""

import uuid
from unittest import mock

import pytest

from apps.accounts.services import anonymize_user_account
from apps.core.testing import USER_PASSWORD, assert_error, make_client
from apps.sellers.models import SellerApplication, SellerApplicationStatus, SellerProfile

pytestmark = pytest.mark.django_db

ME = "/api/v1/sellers/me/"


def public_url(profile_id) -> str:
    return f"/api/v1/sellers/{profile_id}/"


def test_public_profile_is_visible_to_anonymous_without_private_data(seller_profile):
    response = make_client().get(public_url(seller_profile.id))

    assert response.status_code == 200, response.content
    body = response.json()
    assert set(body) == {
        "id",
        "venture_name",
        "description",
        "logo_url",
        "avg_rating",
        "reviews_count",
        "releases_count",
        "created_at",
    }
    assert body["avg_rating"] == "0.00"
    assert body["releases_count"] == 0
    assert "contact_phone" not in body


def test_public_profile_still_requires_the_proxy_secret(seller_profile):
    response = make_client(proxy=False).get(public_url(seller_profile.id))
    assert_error(response, 403, "FORBIDDEN_PROXY")


def test_inactive_or_unknown_profile_returns_404(seller_profile):
    SellerProfile.objects.filter(pk=seller_profile.pk).update(is_active=False)

    assert_error(make_client().get(public_url(seller_profile.id)), 404, "NOT_FOUND")
    assert_error(make_client().get(public_url(uuid.uuid4())), 404, "NOT_FOUND")


def test_active_seller_updates_allowed_fields_only(logged_client, seller_profile):
    response = logged_client.patch(
        ME,
        {
            "venture_name": "Brownies Premium",
            "contact_phone": "+593 99 123 4567",
            "logo_url": "https://evil.example.com/logo.png",
            "logo_public_id": "evil",
            "avg_rating": "5.00",
            "is_active": False,
        },
        format="json",
    )

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["venture_name"] == "Brownies Premium"
    assert body["contact_phone"] == "+593 99 123 4567"
    seller_profile.refresh_from_db()
    assert seller_profile.venture_name == "Brownies Premium"
    assert seller_profile.logo_url is None and seller_profile.logo_public_id is None
    assert str(seller_profile.avg_rating) == "0.00"
    assert seller_profile.is_active is True


def test_patch_me_rejects_non_sellers(logged_client, user):
    assert_error(logged_client.patch(ME, {"venture_name": "x"}, format="json"), 403, "NOT_A_SELLER")


def test_patch_me_rejects_inactive_sellers(logged_client, seller_profile):
    SellerProfile.objects.filter(pk=seller_profile.pk).update(is_active=False)
    assert_error(logged_client.patch(ME, {"venture_name": "x"}, format="json"), 403, "NOT_A_SELLER")


def test_patch_me_requires_authentication(csrf_client, seller_profile):
    assert_error(
        csrf_client.patch(ME, {"venture_name": "x"}, format="json"), 403, "NOT_AUTHENTICATED"
    )


def test_patch_me_without_csrf_is_rejected(logged_client, seller_profile):
    del logged_client.defaults["HTTP_X_CSRFTOKEN"]
    assert_error(logged_client.patch(ME, {"venture_name": "x"}, format="json"), 403, "CSRF_FAILED")
    seller_profile.refresh_from_db()
    assert seller_profile.venture_name == "Brownies de Ana"


def test_patch_me_validates_format(logged_client, seller_profile):
    body = assert_error(
        logged_client.patch(ME, {"venture_name": "", "contact_phone": "abc"}, format="json"),
        400,
        "VALIDATION_ERROR",
    )
    assert {"venture_name", "contact_phone"} <= set(body["details"])


def test_public_profile_returns_404_after_account_deletion(
    logged_client, seller_profile, pending_application
):
    SellerApplication.objects.filter(pk=pending_application.pk).update(
        status=SellerApplicationStatus.APPROVED
    )
    assert make_client().get(public_url(seller_profile.id)).status_code == 200

    response = logged_client.post(
        "/api/v1/auth/me/delete/", {"current_password": USER_PASSWORD}, format="json"
    )

    assert response.status_code == 204, response.content
    assert_error(make_client().get(public_url(seller_profile.id)), 404, "NOT_FOUND")
    seller_profile.refresh_from_db()
    assert seller_profile.is_active is False
    assert seller_profile.contact_phone == ""
    assert seller_profile.user.is_active is False  # el perfil se conserva, desactivado
    pending_application.refresh_from_db()
    assert pending_application.contact_phone == ""
    assert pending_application.instagram_handle == ""
    assert pending_application.venture_name == "Brownies de Ana"  # historial conservado


def test_profile_deactivation_rolls_back_with_failed_anonymization(
    seller_profile, pending_application
):
    with (
        mock.patch("apps.accounts.services.record_audit", side_effect=RuntimeError("boom")),
        pytest.raises(RuntimeError),
    ):
        anonymize_user_account(seller_profile.user)

    seller_profile.refresh_from_db()
    assert seller_profile.is_active is True
    assert seller_profile.contact_phone == "0991234567"
    pending_application.refresh_from_db()
    assert pending_application.contact_phone == "0991234567"
    assert pending_application.instagram_handle == "browniesana"


def test_anonymizing_applicant_without_profile_clears_application_contact_data(
    logged_client, pending_application
):
    SellerApplication.objects.create(
        user=pending_application.user,
        venture_name="Intento previo",
        description="x",
        contact_phone="0980000000",
        instagram_handle="previo",
        status=SellerApplicationStatus.REJECTED,
        rejection_reason="Falta información",
    )

    response = logged_client.post(
        "/api/v1/auth/me/delete/", {"current_password": USER_PASSWORD}, format="json"
    )

    assert response.status_code == 204, response.content
    assert not SellerProfile.objects.exists()
    applications = SellerApplication.objects.filter(user=pending_application.user)
    assert applications.count() == 2
    assert set(applications.values_list("contact_phone", "instagram_handle")) == {("", "")}


# --- GET /api/v1/sellers/me/ ------------------------------------------------------------------


def test_get_me_returns_own_profile_with_contact_phone(logged_client, seller_profile):
    response = logged_client.get(ME)

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["id"] == str(seller_profile.id)
    assert body["contact_phone"] == "0991234567"
    assert body["is_active"] is True
    assert set(body) == {
        "id",
        "venture_name",
        "description",
        "logo_url",
        "contact_phone",
        "avg_rating",
        "reviews_count",
        "releases_count",
        "is_active",
        "created_at",
        "updated_at",
    }


def test_get_me_rejects_non_sellers(logged_client, user):
    assert_error(logged_client.get(ME), 403, "NOT_A_SELLER")


def test_get_me_rejects_inactive_sellers(logged_client, seller_profile):
    SellerProfile.objects.filter(pk=seller_profile.pk).update(is_active=False)
    assert_error(logged_client.get(ME), 403, "NOT_A_SELLER")


def test_get_me_requires_authentication(api_client, seller_profile):
    assert_error(api_client.get(ME), 403, "NOT_AUTHENTICATED")
