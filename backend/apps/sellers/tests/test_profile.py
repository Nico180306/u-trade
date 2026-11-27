"""Perfil público (AllowAny) y edición restringida a vendedor activo."""

import uuid

import pytest

from apps.core.testing import assert_error, make_client
from apps.sellers.models import SellerProfile

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
        "created_at",
    }
    assert body["avg_rating"] == "0.00"
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
