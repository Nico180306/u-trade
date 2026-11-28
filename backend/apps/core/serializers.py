from rest_framework import serializers

from apps.core.exceptions import ErrorCode


class ErrorResponseSerializer(serializers.Serializer):
    """Formato uniforme de errores de la API (solo documentación OpenAPI)."""

    code = serializers.ChoiceField(choices=ErrorCode.choices)
    message = serializers.CharField()
    details = serializers.DictField()
