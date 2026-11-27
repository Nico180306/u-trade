"""Casos de uso de identidad (Auth Core + verificación OTP). Única capa de accounts que muta
estado."""

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status

from apps.accounts import selectors
from apps.accounts.managers import normalize_email_address
from apps.accounts.models import EmailVerificationOTP, OTPPurpose, User
from apps.accounts.validators import is_disposable_email, is_uisek_email
from apps.core.email import EmailService
from apps.core.exceptions import DomainError
from apps.core.services import record_audit

ANONYMIZED_FULL_NAME = "Usuario eliminado"
ANONYMIZED_EMAIL_DOMAIN = "anon.utrade.local"
_AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


def _validate_new_password(password: str, user: User, *, field: str = "password") -> None:
    """Aplica AUTH_PASSWORD_VALIDATORS. `field` es el nombre del campo del request, para que
    `details` use la misma clave que el serializer (password en registro, new_password en
    reset y cambio)."""
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise DomainError(
            "VALIDATION_ERROR",
            "Los datos enviados no son válidos.",
            details={field: list(exc.messages)},
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
    _validate_new_password(new_password, user, field="new_password")
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
    _validate_new_password(new_password, user, field="new_password")
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
    # TODO(acuerdo de equipo): desactivar SellerProfile y anonimizar sus datos de contacto
    #   vía sellers.services (fuera del alcance de feature/verification-sellers-be).

    locked.email = f"deleted_{locked.id.hex}@{ANONYMIZED_EMAIL_DOMAIN}"
    locked.full_name = ANONYMIZED_FULL_NAME
    locked.phone_number = ""
    locked.uisek_email = None
    locked.uisek_email_verified_at = None
    locked.is_active = False
    locked.set_unusable_password()
    locked.save()

    record_audit(actor=locked, action="USER_ANONYMIZED", entity_type="User", entity_id=locked.id)


# --- Verificación de correo por OTP (BUYER_EMAIL / UISEK_SELLER) -----------------------------

OTP_SEND_WINDOW = timedelta(minutes=15)


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def otp_code_hash(*, user_id, purpose: str, target_email: str, code: str) -> str:
    message = f"{user_id}:{purpose}:{target_email.lower()}:{code}"
    return hmac.new(
        settings.OTP_SIGNING_SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()


def _otp_target_email(user: User, purpose: str, target_email: str | None) -> str:
    """Resuelve y valida el correo destino del OTP antes de abrir la transacción."""
    if purpose == OTPPurpose.BUYER_EMAIL:
        if user.email_verified_at is not None:
            raise DomainError("EMAIL_ALREADY_VERIFIED", "Tu correo ya está verificado.")
        return normalize_email_address(user.email)

    target = normalize_email_address(target_email or "")
    if not is_uisek_email(target):
        raise DomainError(
            "INVALID_UISEK_EMAIL",
            "Debes usar tu correo institucional @uisek.edu.ec.",
            details={"uisek_email": ["Solo se admite el dominio exacto @uisek.edu.ec."]},
        )
    if user.uisek_email_verified_at is not None:
        raise DomainError("UISEK_ALREADY_VERIFIED", "Tu correo UISEK ya está verificado.")
    if selectors.uisek_email_claimed_by_other(target, exclude_user_id=user.id):
        raise DomainError(
            "UISEK_EMAIL_ALREADY_IN_USE",
            "Este correo UISEK ya está vinculado a otra cuenta.",
            status_code=status.HTTP_409_CONFLICT,
        )
    return target


def request_email_otp(
    user: User, purpose: str, target_email: str | None = None
) -> EmailVerificationOTP:
    """Emite un OTP nuevo para (user, purpose), invalidando el anterior.

    El conteo de envíos de los últimos 15 min ocurre con el User bloqueado, de modo que dos
    peticiones concurrentes no pueden superar OTP_MAX_SENDS_PER_15MIN. El correo sale solo tras
    el commit y el código en claro nunca se persiste.
    """
    target = _otp_target_email(user, purpose, target_email)

    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        now = timezone.now()

        recent_sends = list(
            EmailVerificationOTP.objects.filter(
                user=locked, purpose=purpose, created_at__gte=now - OTP_SEND_WINDOW
            )
            .order_by("created_at")
            .values_list("created_at", flat=True)
        )
        if len(recent_sends) >= settings.OTP_MAX_SENDS_PER_15MIN:
            retry_after = recent_sends[0] + OTP_SEND_WINDOW - now
            raise DomainError(
                "OTP_RATE_LIMITED",
                "Alcanzaste el máximo de códigos enviados. Intenta más tarde.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                details={"retry_after_seconds": max(int(retry_after.total_seconds()), 1)},
            )

        EmailVerificationOTP.objects.filter(
            user=locked, purpose=purpose, consumed_at__isnull=True
        ).update(consumed_at=now, updated_at=now)

        code = generate_otp_code()
        otp = EmailVerificationOTP.objects.create(
            user=locked,
            purpose=purpose,
            target_email=target,
            code_hash=otp_code_hash(
                user_id=locked.id, purpose=purpose, target_email=target, code=code
            ),
            expires_at=now + timedelta(minutes=settings.OTP_TTL_MINUTES),
        )
        ttl = settings.OTP_TTL_MINUTES
        transaction.on_commit(lambda: EmailService.send_otp_email(target, code, purpose, ttl))
    return otp


def _apply_uisek_verification(user: User, uisek_email: str, now) -> None:
    user.uisek_email = uisek_email
    user.uisek_email_verified_at = now


def verify_email_otp(user: User, purpose: str, code: str) -> User:
    """Valida el último OTP activo de (user, purpose) en tiempo constante.

    Un código incorrecto incrementa attempts_count (y al 5.º intento fija consumed_at): ese
    cambio debe confirmarse, así que el DomainError se lanza DESPUÉS de cerrar la transacción.
    """
    failure: DomainError | None = None

    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        otp = (
            EmailVerificationOTP.objects.select_for_update()
            .filter(user=locked, purpose=purpose, consumed_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
        now = timezone.now()
        stale_target = (
            otp is not None
            and purpose == OTPPurpose.BUYER_EMAIL
            and otp.target_email != normalize_email_address(locked.email)
        )
        if otp is None or otp.expires_at <= now or stale_target:
            raise DomainError(
                "OTP_EXPIRED_OR_INVALID", "El código expiró o no existe. Solicita uno nuevo."
            )

        expected = otp_code_hash(
            user_id=locked.id, purpose=purpose, target_email=otp.target_email, code=code
        )
        if not hmac.compare_digest(expected, otp.code_hash):
            otp.attempts_count += 1
            if otp.attempts_count >= settings.OTP_MAX_ATTEMPTS:
                otp.consumed_at = now
                record_audit(
                    actor=locked,
                    action="OTP_LOCKED",
                    entity_type="EmailVerificationOTP",
                    entity_id=otp.id,
                    metadata={"purpose": purpose},
                )
                failure = DomainError(
                    "OTP_LOCKED", "Demasiados intentos fallidos. Solicita un código nuevo."
                )
            else:
                failure = DomainError(
                    "OTP_INVALID",
                    "El código no es correcto.",
                    details={"attempts_remaining": settings.OTP_MAX_ATTEMPTS - otp.attempts_count},
                )
            otp.save(update_fields=["attempts_count", "consumed_at", "updated_at"])
        else:
            otp.consumed_at = now
            otp.save(update_fields=["consumed_at", "updated_at"])
            _complete_verification(locked, otp, now)

    if failure is not None:
        raise failure
    return locked


def _complete_verification(user: User, otp: EmailVerificationOTP, now) -> None:
    """Aplica el resultado de un OTP correcto. Se ejecuta dentro de la transacción de verify."""
    uisek_shortcut = False

    if otp.purpose == OTPPurpose.BUYER_EMAIL:
        user.email_verified_at = now
        email = normalize_email_address(user.email)
        # Atajo UX: registrarse con @uisek.edu.ec y verificarlo cubre también la verificación
        # de vendedor, salvo que ese correo ya esté reclamado por otra cuenta.
        if (
            is_uisek_email(email)
            and user.uisek_email_verified_at is None
            and not selectors.uisek_email_claimed_by_other(email, exclude_user_id=user.id)
        ):
            _apply_uisek_verification(user, email, now)
            uisek_shortcut = True
        action = "EMAIL_VERIFIED"
    else:
        if selectors.uisek_email_claimed_by_other(otp.target_email, exclude_user_id=user.id):
            raise DomainError(
                "UISEK_EMAIL_ALREADY_IN_USE",
                "Este correo UISEK ya está vinculado a otra cuenta.",
                status_code=status.HTTP_409_CONFLICT,
            )
        _apply_uisek_verification(user, normalize_email_address(otp.target_email), now)
        action = "UISEK_EMAIL_VERIFIED"

    try:
        with transaction.atomic():  # savepoint: la carrera del índice único parcial -> 409
            user.save(
                update_fields=[
                    "email_verified_at",
                    "uisek_email",
                    "uisek_email_verified_at",
                    "updated_at",
                ]
            )
    except IntegrityError as exc:
        raise DomainError(
            "UISEK_EMAIL_ALREADY_IN_USE",
            "Este correo UISEK ya está vinculado a otra cuenta.",
            status_code=status.HTTP_409_CONFLICT,
        ) from exc

    record_audit(
        actor=user,
        action=action,
        entity_type="User",
        entity_id=user.id,
        metadata={"purpose": otp.purpose, "uisek_shortcut": uisek_shortcut},
    )
