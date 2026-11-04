from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nueva/", views.crear, name="crear"),
    path("<slug:slug>/", views.detalle, name="detalle"),
    path("<slug:slug>/editar/", views.editar, name="editar"),
    path("<slug:slug>/eliminar/", views.eliminar, name="eliminar"),
]
