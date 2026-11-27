"""Consultas de solo lectura de cuentas."""

import uuid

from apps.accounts.managers import normalize_email_address
from apps.accounts.models import User


def get_user_by_id(user_id: uuid.UUID) -> User | None:
    return User.objects.filter(pk=user_id).first()


def get_active_user_by_email(email: str) -> User | None:
    return User.objects.filter(email=normalize_email_address(email), is_active=True).first()


def email_is_registered(email: str) -> bool:
    return User.objects.filter(email=normalize_email_address(email)).exists()
