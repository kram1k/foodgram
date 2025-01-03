from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from .settings import STATIC_URL, STATIC_ROOT

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
] + static(STATIC_URL, document_root=STATIC_ROOT)
