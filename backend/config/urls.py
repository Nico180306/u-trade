from django.contrib import admin
from django.urls import include, path

from apps.core.views import LegacyHealthView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Alias de compatibilidad del bootstrap; la ruta canónica es /api/v1/health/.
    path("api/health/", LegacyHealthView.as_view(), name="health-legacy"),
    path("api/v1/", include("apps.core.urls")),
]
