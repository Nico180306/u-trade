"""Casos de uso de identidad (Auth Core). Única capa de accounts que muta estado."""

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status

from apps.accounts import selectors
from apps.accounts.managers import normalize_email_address
from apps.accounts.models import User
from apps.accounts.validators import is_disposable_email
from apps.core.email import EmailService
from apps.core.exceptions import DomainError
from apps.core.services import record_audit

ANONYMIZED_FULL_NAME = "Usuario eliminado"
ANONYMIZED_EMAIL_DOMAIN = "anon.utrade.local"
_AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


def _validate_new_password(password: str, user: User) -> None:
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise DomainError(
            "VALIDATION_ERROR",
            "Los datos enviados no son válidos.",
            details={"password": list(exc.messages)},
        ) from exc


# --- Sesiones ---------------------------------------------------------------------------------


def start_session(request, user: User) -> None:
    """Crea la sesión Django (rota la session key para evitar fijación de sesión)."""
    login(request, user, backend=_AUTH_BACKEND)


def end_session(request) -> None:
    logout(request)


# --- Registro y login -------------------------------------------------------------------------


@transaction.atomic
def register_user(
    *,
    email: str,
    password: str,
    accept_terms: bool,
    accept_privacy: bool,
    full_name: str = "",
    phone_number: str = "",
) -> User:
    if not (accept_terms and accept_privacy):
        raise DomainError(
            "CONSENT_REQUIRED",
            "Debes aceptar los Términos y la Política de Privacidad.",
            details={"accept_terms": accept_terms, "accept_privacy": accept_privacy},
        )

    email = normalize_email_address(email)
    if is_disposable_email(email):
        raise DomainError("DISPOSABLE_EMAIL", "No se permiten correos temporales o desechables.")
    if selectors.email_is_registered(email):
        raise DomainError(
            "EMAIL_ALREADY_REGISTERED",
            "Ya existe una cuenta con este correo.",
            status_code=status.HTTP_409_CONFLICT,
        )

    _validate_new_password(password, User(email=email, full_name=full_name))

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=email, password=password, full_name=full_name, phone_number=phone_number
            )
    except IntegrityError as exc:  # carrera entre dos registros simultáneos del mismo email
        raise DomainError(
            "EMAIL_ALREADY_REGISTERED",
            "Ya existe una cuenta con este correo.",
            status_code=status.HTTP_409_CONFLICT,
        ) from exc

    # Evidencia de consentimiento LOPDP sin datos personales.
    record_audit(
        actor=user,
        action="USER_REGISTERED",
        entity_type="User",
        entity_id=user.id,
        metadata={"terms_accepted": True, "privacy_accepted": True},
    )
    return user


def login_user(request, *, email: str, password: str) -> User:
    user = authenticate(request, email=normalize_email_address(email), password=password)
    if user is None:  # credenciales inválidas o cuenta inactiva: mismo error genérico
        raise DomainError("INVALID_CREDENTIALS", "Correo o contraseña incorrectos.")
    start_session(request, user)
    return user


# --- Perfil -----------------------------------------------------------------------------------


def update_profile(
    user: User, *, full_name: str | None = None, phone_number: str | None = None
) -> User:
    update_fields = []
    if full_name is not None:
        user.full_name = full_name
        update_fields.append("full_name")
    if phone_number is not None:
        user.phone_number = phone_number
        update_fields.append("phone_number")
    if update_fields:
        user.save(update_fields=[*update_fields, "updated_at"])
    return user


# --- Contraseñas ------------------------------------------------------------------------------


def verify_current_password(user: User, raw_password: str) -> None:
    if not user.check_password(raw_password):
        raise DomainError("INVALID_PASSWORD", "La contraseña actual no es correcta.")


@transaction.atomic
def change_password(request, user: User, *, current_password: str, new_password: str) -> None:
    verify_current_password(user, current_password)
    _validate_new_password(new_password, user)
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    update_session_auth_hash(request, user)  # mantiene la sesión actual, invalida las demás
    record_audit(actor=user, action="PASSWORD_CHANGED", entity_type="User", entity_id=user.id)


def _password_reset_link(user: User) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"


def request_password_reset(*, email: str) -> None:
    """Respuesta neutra: no revela si la cuenta existe. El correo sale solo tras el commit."""
    user = selectors.get_active_user_by_email(email)
    if user is None or not user.has_usable_password():
        return

    link = _password_reset_link(user)
    recipient = user.email
    with transaction.atomic():
        transaction.on_commit(
            lambda: EmailService.send(
                to=recipient,
                subject="U-Trade: restablece tu contraseña",
                body=(
                    "Recibimos una solicitud para restablecer tu contraseña de U-Trade.\n\n"
                    f"Abre este enlace para elegir una nueva: {link}\n\n"
                    "Si no fuiste tú, ignora este correo."
                ),
            )
        )


def _user_from_reset_uid(uid: str) -> User | None:
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = selectors.get_user_by_id(user_id)
    except (TypeError, ValueError, OverflowError, DjangoValidationError):
        return None
    if user is None or not user.is_active:
        return None
    return user


@transaction.atomic
def confirm_password_reset(*, uid: str, token: str, new_password: str) -> None:
    user = _user_from_reset_uid(uid)
    if user is None or not default_token_generator.check_token(user, token):
        raise DomainError("INVALID_RESET_TOKEN", "El enlace de restablecimiento no es válido.")
    _validate_new_password(new_password, user)
    user.set_password(new_password)  # cambia el hash: invalida todas las sesiones previas
    user.save(update_fields=["password", "updated_at"])
    record_audit(actor=user, action="PASSWORD_RESET", entity_type="User", entity_id=user.id)


# --- Anonimización LOPDP ----------------------------------------------------------------------


@transaction.atomic
def anonymize_user_account(user: User) -> None:
    """Anonimiza la cuenta preservando la integridad referencial histórica.

    Las sesiones quedan invalidadas porque cambia el hash de contraseña (HASH_SESSION_KEY ya no
    coincide) y porque ModelBackend rechaza usuarios con is_active=False.
    """
    locked = User.objects.select_for_update().get(pk=user.pk)

    # TODO(feature/sales-management-be): bloquear si el vendedor tiene ventas PUBLISHED
    #   activas o futuras (DomainError), antes de cualquier modificación.
    # TODO(feature/reservations-engine-be): cancelar las reservas CONFIRMED del usuario que
    #   correspondan, restaurando stock vía reservations.services.

    locked.email = f"deleted_{locked.id.hex}@{ANONYMIZED_EMAIL_DOMAIN}"
    locked.full_name = ANONYMIZED_FULL_NAME
    locked.phone_number = ""
    locked.uisek_email = None
    locked.uisek_email_verified_at = None
    locked.is_active = False
    locked.set_unusable_password()
    locked.save()

    record_audit(actor=locked, action="USER_ANONYMIZED", entity_type="User", entity_id=locked.id)
