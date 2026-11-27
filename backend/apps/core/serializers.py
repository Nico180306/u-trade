from rest_framework import serializers


class ErrorResponseSerializer(serializers.Serializer):
    """Formato uniforme de errores de la API (solo documentación OpenAPI)."""

    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField()
