from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.common.urls")),
    path("api/v1/", include("apps.graduate.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
]
