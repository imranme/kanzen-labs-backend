
from django.contrib import admin 
from django.urls import path ,include
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    path(
        "api/docs/",SpectacularSwaggerView.as_view(url_name="schema"),name="swagger-ui",),
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/products/', include('apps.products.urls')),
    path("api/v1/compliance/", include("apps.compliance.urls")),
    path('api/v1/logistics/', include('apps.logistics.urls')),
    path("api/v1/ai/", include("apps.ai_engine.urls")),
    path("api/v1/growth/", include("apps.growth.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)