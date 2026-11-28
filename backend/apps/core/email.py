"""Abstracción única de correo de U-Trade.

Proveedores (settings.EMAIL_PROVIDER):
- "console" (local/test, o si falta RESEND_API_KEY): `django.core.mail.send_mail` hacia el
  EMAIL_BACKEND configurado (consola en local, locmem en tests).
- "resend" (producción): API HTTPS de Resend con `urllib.request` y timeout corto.

REGLA: toda llamada disparada desde una mutación debe registrarse con `transaction.on_commit()`.
Los envíos son best-effort: nunca propagan errores (el commit ya ocurrió) y los logs jamás
incluyen el cuerpo del correo ni códigos OTP.
"""

import json
import logging
import urllib.error
import urllib.request

import sentry_sdk
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_TIMEOUT_SECONDS = 5

OTP_PURPOSE_LABELS = {
    "BUYER_EMAIL": "verificar tu correo de comprador",
    "UISEK_SELLER": "verificar tu correo institucional @uisek.edu.ec",
}


def mask_email(email: str) -> str:
    """ana.perez@example.com -> a***@example.com (para logs, sin PII completa)."""
    local, _, domain = (email or "").partition("@")
    return f"{local[:1]}***@{domain}" if domain else "***"


def _provider() -> str:
    if settings.EMAIL_PROVIDER == "resend" and settings.RESEND_API_KEY:
        return "resend"
    return "console"


class EmailService:
    @classmethod
    def send(cls, *, to: str, subject: str, body: str, category: str = "generic") -> bool:
        """Envía un correo de texto plano. Devuelve False ante cualquier fallo, sin propagarlo."""
        provider = _provider()
        log_extra = {"provider": provider, "category": category, "to": mask_email(to)}
        try:
            if provider == "resend":
                cls._send_via_resend(to=to, subject=subject, body=body)
            else:
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to], fail_silently=False)
        except Exception as exc:  # efecto externo best-effort
            logger.exception("Fallo al enviar correo", extra=log_extra)
            sentry_sdk.capture_exception(exc)
            return False
        logger.info("Correo enviado", extra=log_extra)
        return True

    @staticmethod
    def _send_via_resend(*, to: str, subject: str, body: str) -> None:
        payload = json.dumps(
            {"from": settings.DEFAULT_FROM_EMAIL, "to": [to], "subject": subject, "text": body}
        ).encode()
        request = urllib.request.Request(
            RESEND_API_URL,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "utrade-backend",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=RESEND_TIMEOUT_SECONDS) as response:
                if not 200 <= response.status < 300:
                    raise RuntimeError(f"Resend respondió HTTP {response.status}")
        except urllib.error.HTTPError as exc:
            # Solo se registra el status HTTP, nunca el payload enviado.
            raise RuntimeError(f"Resend respondió HTTP {exc.code}") from None

    # --- Plantillas de dominio ----------------------------------------------------------------

    @classmethod
    def send_otp_email(cls, to_email: str, code: str, purpose: str, ttl_minutes: int) -> bool:
        action = OTP_PURPOSE_LABELS.get(purpose, "verificar tu correo")
        return cls.send(
            to=to_email,
            subject="U-Trade: tu código de verificación",
            body=(
                f"Usa este código para {action} en U-Trade:\n\n"
                f"    {code}\n\n"
                f"El código vence en {ttl_minutes} minutos. "
                "Si no solicitaste este código, ignora este correo."
            ),
            category=f"otp_{purpose.lower()}",
        )

    @classmethod
    def send_seller_application_approved(cls, to_email: str, venture_name: str) -> bool:
        return cls.send(
            to=to_email,
            subject="U-Trade: tu solicitud de vendedor fue aprobada",
            body=(
                f"¡Felicitaciones! Tu emprendimiento «{venture_name}» fue aprobado en U-Trade.\n\n"
                "Ya puedes completar tu perfil de vendedor y programar tus ventas."
            ),
            category="seller_application_approved",
        )

    @classmethod
    def send_seller_application_rejected(
        cls, to_email: str, venture_name: str, reason: str
    ) -> bool:
        return cls.send(
            to=to_email,
            subject="U-Trade: tu solicitud de vendedor no fue aprobada",
            body=(
                f"Revisamos la solicitud de tu emprendimiento «{venture_name}» y por ahora no "
                f"fue aprobada.\n\nMotivo: {reason}\n\n"
                "Puedes corregir lo indicado y enviar una nueva solicitud."
            ),
            category="seller_application_rejected",
        )
