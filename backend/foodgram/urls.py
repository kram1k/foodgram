from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

from api.views import redirect_to_recipe_detail

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<slug:code>/',
        redirect_to_recipe_detail,
        name='redirect_to_recipe_detail'
    ),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'docs/swagger/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),
    path(
        'docs/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
]

if settings.DEBUG:
    urlpatterns += path('__debug__/', include('debug_toolbar.urls'))
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
