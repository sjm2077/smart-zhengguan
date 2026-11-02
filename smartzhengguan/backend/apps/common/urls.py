from django.urls import path

from apps.common.views import ApiIndexView, HealthCheckView


urlpatterns = [
    path("", ApiIndexView.as_view(), name="api-index"),
    path("health/", HealthCheckView.as_view(), name="health-check"),
]
