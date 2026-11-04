from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.ver_canasta, name="ver_canasta"),
    path("agregar/<int:pk>/", views.agregar, name="agregar"),
    path("actualizar/<int:pk>/", views.actualizar, name="actualizar"),
    path("quitar/<int:pk>/", views.quitar, name="quitar"),
    path("vaciar/", views.vaciar, name="vaciar"),
    path("checkout/", views.checkout, name="checkout"),
    path("comprobante/", views.comprobante, name="comprobante"),
    path("comprobante/cerrar/", views.cerrar_comprobante, name="cerrar_comprobante"),
]
