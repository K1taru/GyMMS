from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),     # Currently where the root, landing page
    path("dashboard/", include("dashboard.urls")),
    path("memberships/", include("memberships.urls")),
    path("metrics/", include("metrics.urls")),
    path("payments/", include("payments.urls")),
    path("users/", include("users.urls")),
    
]

# Always serve media files (even in production for now) - in future, use proper media server/CDN 
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # production staticfiles serving
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
