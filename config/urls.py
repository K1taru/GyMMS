from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),     # Currently where the root, landing page
    path("dashboard/", include("dashboard.urls")),
    path("memberships/", include("memberships.urls")),
    path("metrics/", include("metrics.urls")),
    path("payments/", include("payments.urls")),
    path("users/", include("users.urls")),
    
]

# WhiteNoise serves collected static assets under Gunicorn, including DEBUG=False.
# Preserve the existing small-deployment upload serving until a media server is configured.
urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
