from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from apps.accounts.managers import UserManager
from apps.core.models import BaseModel


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    """Usuario de U-Trade. Roles derivados: comprador (autenticado), vendedor (SellerProfile
    activo, apps.sellers) y admin (is_staff)."""

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

    @property
    def active_seller_profile(self):
        """SellerProfile activo o None. Usa la relación inversa sin importar apps.sellers
        (RelatedObjectDoesNotExist hereda de AttributeError). Solo lectura."""
        profile = getattr(self, "seller_profile", None)
        return profile if profile is not None and profile.is_active else None

    @property
    def is_seller(self) -> bool:
        return self.active_seller_profile is not None

    @property
    def seller_profile_id(self):
        profile = self.active_seller_profile
        return profile.id if profile is not None else None


class OTPPurpose(models.TextChoices):
    BUYER_EMAIL = "BUYER_EMAIL", "Correo personal del comprador"
    UISEK_SELLER = "UISEK_SELLER", "Correo institucional del vendedor"


class EmailVerificationOTP(BaseModel):
    """Código OTP de 6 dígitos. Solo se persiste su HMAC-SHA256, nunca el código en claro.

    Sin CHECK duro en attempts_count: al alcanzar OTP_MAX_ATTEMPTS el servicio fija
    consumed_at = now() y responde OTP_LOCKED.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_otps")
    purpose = models.CharField(max_length=20, choices=OTPPurpose.choices)
    target_email = models.EmailField(max_length=254)
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts_count = models.PositiveIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "OTP de verificación de correo"
        verbose_name_plural = "OTP de verificación de correo"
        indexes = [
            models.Index(
                fields=["user", "purpose", "-created_at"], name="otp_user_purpose_created"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.purpose} · {self.user_id}"
