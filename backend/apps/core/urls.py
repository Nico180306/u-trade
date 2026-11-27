from django.urls import path

from apps.core.views import CronSweepView, HealthView

app_name = "core"

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("cron/sweep/", CronSweepView.as_view(), name="cron-sweep"),
]
