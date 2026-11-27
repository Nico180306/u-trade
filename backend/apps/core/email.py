"""Abstracción única de correo. Consola en local, locmem en tests y SMTP de Resend en producción.

Toda llamada disparada desde una mutación debe registrarse con `transaction.on_commit()`.
"""

import logging

import sentry_sdk
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send(*, to: str, subject: str, body: str) -> bool:
        """Envía un correo de texto plano. Nunca propaga errores: el commit ya ocurrió."""
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to], fail_silently=False)
        except Exception as exc:  # el envío es un efecto externo best-effort
            logger.exception("Fallo al enviar correo", extra={"subject": subject})
            sentry_sdk.capture_exception(exc)
            return False
        return True
