from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/reports/home/", permanent=False)),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls", namespace="users")),
    path("reports/", include("reports.urls", namespace="reports")),
    path("clients/", include("clients.urls", namespace="clients")),
    path("mailings/", include("mailings.urls", namespace="mailings")),
    path("campaigns/", include("campaigns.urls", namespace="campaigns")),
    path("management_panel/", include("management_panel.urls", namespace="management_panel")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
