"""Errores de dominio y formato uniforme de errores de la API: {"code", "message", "details"}."""

import logging
from typing import Any

import sentry_sdk
from django.conf import settings
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Error de regla de negocio lanzado desde services.py y traducido a HTTP por el handler."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def error_payload(code: str, message: str, details: dict[str, Any] | None = None) -> dict:
    return {"code": code, "message": message, "details": details or {}}


_DRF_ERRORS: dict[type[exceptions.APIException], tuple[str, str]] = {
    exceptions.ValidationError: ("VALIDATION_ERROR", "Los datos enviados no son válidos."),
    exceptions.ParseError: ("PARSE_ERROR", "El cuerpo de la petición no es JSON válido."),
    exceptions.NotAuthenticated: ("NOT_AUTHENTICATED", "Debes iniciar sesión."),
    exceptions.AuthenticationFailed: ("NOT_AUTHENTICATED", "Debes iniciar sesión."),
    exceptions.PermissionDenied: ("PERMISSION_DENIED", "No tienes permiso para esta acción."),
    exceptions.NotFound: ("NOT_FOUND", "Recurso no encontrado."),
    exceptions.MethodNotAllowed: ("METHOD_NOT_ALLOWED", "Método HTTP no permitido."),
    exceptions.NotAcceptable: ("NOT_ACCEPTABLE", "Formato de respuesta no soportado."),
    exceptions.UnsupportedMediaType: ("UNSUPPORTED_MEDIA_TYPE", "Tipo de contenido no soportado."),
    exceptions.Throttled: ("THROTTLED", "Demasiadas solicitudes. Intenta más tarde."),
}


def _code_and_message(exc: exceptions.APIException) -> tuple[str, str]:
    if isinstance(exc, exceptions.PermissionDenied) and str(exc.detail).startswith("CSRF Failed"):
        return "CSRF_FAILED", "Token CSRF ausente o inválido."
    for exc_class, mapping in _DRF_ERRORS.items():
        if isinstance(exc, exc_class):
            return mapping
    return str(exc.default_code).upper(), str(exc.detail)


def _details(exc: exceptions.APIException, data: Any) -> dict[str, Any]:
    if isinstance(exc, exceptions.ValidationError):
        return data if isinstance(data, dict) else {"non_field_errors": data}
    if isinstance(exc, exceptions.Throttled) and exc.wait is not None:
        return {"wait_seconds": int(exc.wait)}
    return {}


def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    if isinstance(exc, DomainError):
        return Response(error_payload(exc.code, exc.message, exc.details), status=exc.status_code)

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)
    if response is None:
        logger.exception("Excepción no controlada en la API", exc_info=exc)
        sentry_sdk.capture_exception(exc)
        if settings.DEBUG:
            return None
        return Response(
            error_payload("INTERNAL_ERROR", "Error interno del servidor."),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code, message = _code_and_message(exc)
    response.data = error_payload(code, message, _details(exc, response.data))
    return response
