import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_auth_user_model_is_frozen_to_accounts_user():
    assert get_user_model() is User


def test_create_user_uses_uuid_pk_and_normalizes_email():
    user = User.objects.create_user(email="  Ana.Perez@Example.COM ", password="x")

    assert isinstance(user.id, uuid.UUID)
    assert user.email == "ana.perez@example.com"
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.is_email_verified is False
    assert user.is_uisek_verified is False


def test_create_superuser_sets_flags():
    admin = User.objects.create_superuser(email="admin@example.com", password="x")
    assert admin.is_staff is True
    assert admin.is_superuser is True


def test_email_is_unique_case_insensitively():
    User.objects.create_user(email="ana@example.com", password="x")

    with pytest.raises(IntegrityError), transaction.atomic():
        User(email="ANA@example.com").save()  # salta el manager a propósito


def test_uisek_email_unique_only_when_not_null():
    User.objects.create_user(email="a@example.com", password="x")
    User.objects.create_user(email="b@example.com", password="x")  # dos NULL permitidos
    User.objects.create_user(email="c@example.com", password="x", uisek_email="c@uisek.edu.ec")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(email="d@example.com", password="x", uisek_email="c@uisek.edu.ec")
