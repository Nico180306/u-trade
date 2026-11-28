from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import BaseModel


class SellerApplicationStatus(models.TextChoices):
    PENDING = "PENDING", "Pendiente"
    APPROVED = "APPROVED", "Aprobada"
    REJECTED = "REJECTED", "Rechazada"


class SellerApplication(BaseModel):
    """Solicitud de un estudiante UISEK verificado para vender. Sus cambios de estado ocurren
    exclusivamente en sellers.services (incluidas las acciones del Django Admin)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_applications"
    )
    venture_name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    contact_phone = models.CharField(max_length=20)
    instagram_handle = models.CharField(max_length=50, blank=True, default="")
    status = models.CharField(
        max_length=10,
        choices=SellerApplicationStatus.choices,
        default=SellerApplicationStatus.PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_seller_applications",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "solicitud de vendedor"
        verbose_name_plural = "solicitudes de vendedor"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="PENDING"),
                name="unique_pending_seller_application_per_user",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.venture_name} ({self.get_status_display()})"


class SellerProfile(BaseModel):
    """Perfil público del emprendimiento. Se crea (o reactiva) atómicamente al aprobar una
    SellerApplication. avg_rating / reviews_count / releases_count son calculados por servicios
    de otras ramas (reseñas, reservas) y nunca se editan a mano."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seller_profile"
    )
    venture_name = models.CharField(max_length=100)
    description = models.TextField(max_length=1000)
    logo_url = models.URLField(max_length=500, null=True, blank=True)
    logo_public_id = models.CharField(max_length=255, null=True, blank=True)
    contact_phone = models.CharField(max_length=20)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0.00"))
    reviews_count = models.PositiveIntegerField(default=0)
    releases_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "perfil de vendedor"
        verbose_name_plural = "perfiles de vendedor"

    def __str__(self) -> str:
        return self.venture_name
