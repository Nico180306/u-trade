from django.contrib import admin
from django.db import connection
from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return Response({"status": "ok", "database": "ok"}, status=status.HTTP_200_OK)
    except Exception:
        return Response(
            {"status": "error", "database": "unreachable"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
]
