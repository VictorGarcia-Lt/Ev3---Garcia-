"""Rutas raíz del proyecto VetCare Central."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("catalogo/", include("apps.catalogo.urls")),
    path("canasta/", include("apps.pedidos.urls")),
    path("usuarios/", include("apps.usuarios.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "VetCare Central - Panel de Control"
admin.site.site_title = "VetCare Admin"
admin.site.index_title = "Gestión de productos para mascotas"
