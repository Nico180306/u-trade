from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import error_payload


def _server_time() -> str:
    return serializers.DateTimeField().to_representation(timezone.now())


class HealthView(APIView):
    """Health check público (exento del secreto de proxy). Solo lectura."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="health_check",
        tags=["core"],
        responses={
            200: inline_serializer(
                "HealthResponse",
                {
                    "status": serializers.CharField(),
                    "database": serializers.CharField(),
                    "server_time": serializers.DateTimeField(),
                },
            ),
            503: inline_serializer(
                "HealthUnavailableResponse",
                {
                    "status": serializers.CharField(),
                    "database": serializers.CharField(),
                    "server_time": serializers.DateTimeField(),
                },
            ),
        },
    )
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:  # cualquier fallo de DB se reporta como 503
            return Response(
                {"status": "error", "database": "unreachable", "server_time": _server_time()},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"status": "ok", "database": "ok", "server_time": _server_time()})


@extend_schema_view(get=extend_schema(exclude=True))
class LegacyHealthView(HealthView):
    """Alias /api/health/ del bootstrap, fuera del contrato OpenAPI."""


class CronSweepView(APIView):
    """Barrido periódico invocado por GitHub Actions. El middleware exige X-Cron-Secret."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="cron_sweep",
        tags=["core"],
        request=None,
        responses={
            200: inline_serializer(
                "CronSweepResponse",
                {"status": serializers.CharField(), "processed": serializers.IntegerField()},
            )
        },
    )
    def post(self, request):
        # TODO(feature/penalties-be): invocar penalties.services.materialize_no_shows().
        return Response({"status": "ok", "processed": 0})


def csrf_failure(request, reason: str = ""):
    """CSRF_FAILURE_VIEW: mantiene el formato uniforme de errores también en fallos de CSRF."""
    return JsonResponse(error_payload("CSRF_FAILED", "Token CSRF ausente o inválido."), status=403)
