"""Casos de uso de vendedores UISEK. Única capa de sellers que muta estado (también para las
acciones del Django Admin)."""

import uuid

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status

from apps.accounts.models import User
from apps.core.email import EmailService
from apps.core.exceptions import DomainError
from apps.core.services import record_audit
from apps.sellers.models import SellerApplication, SellerApplicationStatus, SellerProfile

PROFILE_EDITABLE_FIELDS = ("venture_name", "description", "contact_phone")


def _pending_error() -> DomainError:
    return DomainError(
        "SELLER_APPLICATION_ALREADY_PENDING",
        "Ya tienes una solicitud de vendedor pendiente de revisión.",
        status_code=status.HTTP_409_CONFLICT,
    )


def _not_found() -> DomainError:
    return DomainError(
        "NOT_FOUND", "Solicitud no encontrada.", status_code=status.HTTP_404_NOT_FOUND
    )


def _require_staff(admin_user: User) -> None:
    if not (admin_user and admin_user.is_active and admin_user.is_staff):
        raise DomainError(
            "PERMISSION_DENIED",
            "Solo un administrador puede revisar solicitudes.",
            status_code=status.HTTP_403_FORBIDDEN,
        )


def _lock_pending_application(application_id: uuid.UUID) -> SellerApplication:
    application = SellerApplication.objects.select_for_update().filter(pk=application_id).first()
    if application is None:
        raise _not_found()
    if application.status != SellerApplicationStatus.PENDING:
        raise DomainError(
            "SELLER_APPLICATION_NOT_PENDING",
            "La solicitud ya fue revisada.",
            status_code=status.HTTP_409_CONFLICT,
            details={"status": application.status},
        )
    return application


# --- Solicitud -------------------------------------------------------------------------------


def submit_seller_application(
    user: User,
    *,
    venture_name: str,
    description: str,
    contact_phone: str,
    instagram_handle: str = "",
) -> SellerApplication:
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)

        if locked.uisek_email_verified_at is None:
            raise DomainError(
                "UISEK_NOT_VERIFIED",
                "Debes verificar tu correo @uisek.edu.ec antes de postular como vendedor.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if SellerProfile.objects.filter(user=locked, is_active=True).exists():
            raise DomainError(
                "ALREADY_A_SELLER",
                "Ya eres vendedor en U-Trade.",
                status_code=status.HTTP_409_CONFLICT,
            )
        if SellerApplication.objects.filter(
            user=locked, status=SellerApplicationStatus.PENDING
        ).exists():
            raise _pending_error()

        try:
            with transaction.atomic():  # savepoint: respaldo del índice único parcial
                application = SellerApplication.objects.create(
                    user=locked,
                    venture_name=venture_name,
                    description=description,
                    contact_phone=contact_phone,
                    instagram_handle=instagram_handle,
                )
        except IntegrityError as exc:
            raise _pending_error() from exc

        record_audit(
            actor=locked,
            action="SELLER_APPLICATION_SUBMITTED",
            entity_type="SellerApplication",
            entity_id=application.id,
        )
    return application


# --- Revisión (Django Admin) -----------------------------------------------------------------


def approve_seller_application(application_id: uuid.UUID, admin_user: User) -> SellerProfile:
    """Aprueba la solicitud y crea (o reactiva/actualiza) el SellerProfile en la misma
    transacción. El correo al solicitante sale solo tras el commit."""
    _require_staff(admin_user)
    applicant_id = (
        SellerApplication.objects.filter(pk=application_id)
        .values_list("user_id", flat=True)
        .first()
    )
    if applicant_id is None:
        raise _not_found()

    with transaction.atomic():
        # Mismo orden de bloqueo que submit_seller_application: User -> SellerApplication.
        applicant = User.objects.select_for_update().get(pk=applicant_id)
        application = _lock_pending_application(application_id)

        if not applicant.is_active or applicant.uisek_email_verified_at is None:
            raise DomainError(
                "UISEK_NOT_VERIFIED",
                "El solicitante ya no tiene un correo UISEK verificado o su cuenta está inactiva.",
                status_code=status.HTTP_409_CONFLICT,
            )

        now = timezone.now()
        application.status = SellerApplicationStatus.APPROVED
        application.reviewed_by = admin_user
        application.reviewed_at = now
        application.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])

        profile = SellerProfile.objects.filter(user=applicant).first()
        if profile is None:
            profile = SellerProfile.objects.create(
                user=applicant,
                venture_name=application.venture_name,
                description=application.description,
                contact_phone=application.contact_phone,
            )
        else:
            profile.venture_name = application.venture_name
            profile.description = application.description
            profile.contact_phone = application.contact_phone
            profile.is_active = True
            profile.save(
                update_fields=[
                    "venture_name",
                    "description",
                    "contact_phone",
                    "is_active",
                    "updated_at",
                ]
            )

        record_audit(
            actor=admin_user,
            action="SELLER_APPLICATION_APPROVED",
            entity_type="SellerApplication",
            entity_id=application.id,
            metadata={"seller_profile_id": str(profile.id)},
        )
        to_email, venture_name = applicant.email, application.venture_name
        transaction.on_commit(
            lambda: EmailService.send_seller_application_approved(to_email, venture_name)
        )
    return profile


def reject_seller_application(
    application_id: uuid.UUID, admin_user: User, rejection_reason: str
) -> SellerApplication:
    _require_staff(admin_user)
    reason = (rejection_reason or "").strip()
    if not reason:
        raise DomainError(
            "REJECTION_REASON_REQUIRED",
            "Debes indicar el motivo del rechazo.",
            details={"rejection_reason": ["Este campo es obligatorio."]},
        )

    with transaction.atomic():
        application = _lock_pending_application(application_id)
        application.status = SellerApplicationStatus.REJECTED
        application.reviewed_by = admin_user
        application.reviewed_at = timezone.now()
        application.rejection_reason = reason
        application.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "rejection_reason",
                "updated_at",
            ]
        )

        record_audit(
            actor=admin_user,
            action="SELLER_APPLICATION_REJECTED",
            entity_type="SellerApplication",
            entity_id=application.id,
        )
        to_email = User.objects.values_list("email", flat=True).get(pk=application.user_id)
        venture_name = application.venture_name
        transaction.on_commit(
            lambda: EmailService.send_seller_application_rejected(to_email, venture_name, reason)
        )
    return application


# --- Perfil del vendedor ---------------------------------------------------------------------


@transaction.atomic
def update_seller_profile(user: User, **changes) -> SellerProfile:
    """Edita solo venture_name, description y contact_phone. logo_url/logo_public_id se
    escribirán con validación contra Cloudinary en feature/sales-management-be."""
    profile = SellerProfile.objects.select_for_update().filter(user=user, is_active=True).first()
    if profile is None:
        raise DomainError(
            "NOT_A_SELLER",
            "Necesitas un perfil de vendedor activo.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    update_fields = [field for field in PROFILE_EDITABLE_FIELDS if field in changes]
    for field in update_fields:
        setattr(profile, field, changes[field])
    if update_fields:
        profile.save(update_fields=[*update_fields, "updated_at"])
    return profile
