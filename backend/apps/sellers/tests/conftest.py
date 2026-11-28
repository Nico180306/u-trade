import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.core.testing import USER_PASSWORD, bootstrap_csrf, login, make_client
from apps.sellers.models import SellerApplication, SellerProfile

UISEK_EMAIL = "ana@uisek.edu.ec"
STAFF_EMAIL = "admin@example.com"

APPLICATION_DATA = {
    "venture_name": "Brownies de Ana",
    "description": "Brownies caseros con nuez.",
    "contact_phone": "0991234567",
    "instagram_handle": "@browniesana",
}


@pytest.fixture
def uisek_user(user) -> User:
    user.uisek_email = UISEK_EMAIL
    user.uisek_email_verified_at = timezone.now()
    user.save(update_fields=["uisek_email", "uisek_email_verified_at"])
    return user


@pytest.fixture
def staff_user(db) -> User:
    return User.objects.create_user(email=STAFF_EMAIL, password=USER_PASSWORD, is_staff=True)


@pytest.fixture
def pending_application(uisek_user) -> SellerApplication:
    data = {**APPLICATION_DATA, "instagram_handle": "browniesana"}
    return SellerApplication.objects.create(user=uisek_user, **data)


@pytest.fixture
def seller_profile(uisek_user) -> SellerProfile:
    return SellerProfile.objects.create(
        user=uisek_user,
        venture_name="Brownies de Ana",
        description="Brownies caseros con nuez.",
        contact_phone="0991234567",
    )


@pytest.fixture
def other_client(db):
    User.objects.create_user(email="otro@example.com", password=USER_PASSWORD)
    client = bootstrap_csrf(make_client(client_ip="203.0.113.99"))
    assert login(client, email="otro@example.com").status_code == 200
    return client
