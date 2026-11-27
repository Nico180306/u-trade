from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from apps.accounts.managers import UserManager
from apps.core.models import BaseModel


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    """Usuario de U-Trade. Roles derivados: comprador (autenticado), vendedor (SellerProfile
    activo, en feature/verification-sellers-be) y admin (is_staff)."""

    email = models.EmailField(max_length=254, unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    uisek_email = models.EmailField(max_length=254, null=True, blank=True)
    uisek_email_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        constraints = [
            models.UniqueConstraint(
                fields=["uisek_email"],
                condition=Q(uisek_email__isnull=False),
                name="unique_non_null_uisek_email",
            ),
            models.UniqueConstraint(Lower("email"), name="unique_lower_email"),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def is_uisek_verified(self) -> bool:
        return self.uisek_email_verified_at is not None
