"""Vistas de la canasta de compras, checkout y comprobante."""
import secrets

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.catalogo.models import Producto

from .carrito import (
    CLAVE_COMPROBANTE,
    agregar_item,
    actualizar_item,
    calcular_totales,
    descontar_stock,
    obtener_items,
    obtener_items_para_compra,
    quitar_item,
    vaciar_canasta,
)
from .forms import CheckoutForm

ALFABETO_FOLIO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _destino_seguro(request, destino_por_defecto):
    """Evita redirecciones abiertas al volver a la página de origen."""
    destino = request.POST.get("next") or request.GET.get("next")
    if destino and url_has_allowed_host_and_scheme(
        destino,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destino
    return destino_por_defecto


def _mensajes_error(request, error):
    for mensaje in getattr(error, "messages", [str(error)]):
        messages.error(request, mensaje)


def ver_canasta(request):
    """Resumen de la canasta con subtotal, IVA y total estimado."""
    items, invalidos = obtener_items(request.session)
    if invalidos:
        nombres = ", ".join(f"«{p.nombre}»" for p in invalidos)
        messages.warning(
            request,
            "Se retiraron de la canasta los productos que ya no están "
            f"disponibles para compra: {nombres}.",
        )

    contexto = {
        "items": items,
        "totales": calcular_totales(items),
    }
    return render(request, "pedidos/canasta.html", contexto)


@require_POST
def agregar(request, pk):
    """Agrega un producto a la canasta de la sesión."""
    producto = get_object_or_404(
        Producto.objects.select_related("categoria"),
        pk=pk,
    )
    try:
        cantidad_total = agregar_item(
            request.session, producto, request.POST.get("cantidad", 1)
        )
    except ValidationError as error:
        _mensajes_error(request, error)
    else:
        messages.success(
            request,
            f"«{producto.nombre}» se agregó a la canasta. "
            f"Total de este ítem: {cantidad_total}.",
        )
    return redirect(_destino_seguro(request, producto.get_absolute_url()))


@require_POST
def actualizar(request, pk):
    """Actualiza la cantidad de un ítem de la canasta."""
    producto = get_object_or_404(
        Producto.objects.select_related("categoria"),
        pk=pk,
    )
    try:
        nueva_cantidad = actualizar_item(
            request.session, producto, request.POST.get("cantidad", 1)
        )
    except ValidationError as error:
        _mensajes_error(request, error)
    else:
        messages.success(
            request,
            f"Cantidad actualizada: {nueva_cantidad} unidad(es) de «{producto.nombre}».",
        )
    return redirect("pedidos:ver_canasta")


@require_POST
def quitar(request, pk):
    """Elimina un ítem individual de la canasta."""
    producto = get_object_or_404(Producto, pk=pk)
    quitar_item(request.session, producto.pk)
    messages.info(request, f"«{producto.nombre}» fue eliminado de la canasta.")
    return redirect("pedidos:ver_canasta")


@require_POST
def vaciar(request):
    """Vacía la canasta completa de la sesión."""
    vaciar_canasta(request.session)
    messages.info(request, "La canasta de compras fue vaciada por completo.")
    return redirect("pedidos:ver_canasta")


def checkout(request):
    """Checkout de compra: valida stock, descuenta unidades y genera folio."""
    items, invalidos = obtener_items(request.session)
    if invalidos:
        messages.warning(
            request,
            "Algunos ítems dejaron de estar disponibles y fueron retirados de la canasta.",
        )
        return redirect("pedidos:ver_canasta")
    if not items:
        messages.warning(
            request, "Tu canasta está vacía. Agrega productos para continuar."
        )
        return redirect("pedidos:ver_canasta")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            try:
                with transaction.atomic():
                    items, invalidos = obtener_items_para_compra(
                        request.session, bloquear=True
                    )
                    if invalidos or not items:
                        messages.error(
                            request,
                            "La disponibilidad cambió mientras completabas el formulario. "
                            "Revisa tu canasta antes de confirmar.",
                        )
                        return redirect("pedidos:ver_canasta")

                    totales = calcular_totales(items)
                    folio = (
                        f"VET-{timezone.localdate().year}-"
                        f"{''.join(secrets.choice(ALFABETO_FOLIO) for _ in range(4))}"
                    )

                    descontar_stock(items)

                    request.session[CLAVE_COMPROBANTE] = {
                        "folio": folio,
                        "fecha": timezone.localtime().strftime("%d-%m-%Y %H:%M"),
                        "tutor": datos["nombre_tutor"],
                        "email": datos["email"],
                        "telefono": datos["telefono"],
                        "direccion": datos.get("direccion") or "",
                        "observaciones": datos.get("observaciones") or "",
                        "items": [
                            {
                                "codigo": item["producto"].codigo,
                                "nombre": item["producto"].nombre,
                                "categoria": item["producto"].categoria.nombre,
                                "cantidad": item["cantidad"],
                                "precio": str(int(item["producto"].precio)),
                                "subtotal": str(int(item["subtotal"])),
                            }
                            for item in items
                        ],
                        "subtotal": str(int(totales["subtotal"])),
                        "iva": str(int(totales["iva"])),
                        "total": str(int(totales["total"])),
                        "tasa_iva": totales["tasa_iva"],
                    }
                    vaciar_canasta(request.session)
            except ValidationError:
                messages.error(
                    request,
                    "El stock cambió mientras confirmabas la compra. "
                    "Revisa tu canasta e inténtalo nuevamente.",
                )
                return redirect("pedidos:ver_canasta")

            messages.success(
                request,
                f"¡Compra confirmada! Tu comprobante es {folio}.",
            )
            return redirect("pedidos:comprobante")

        messages.error(request, "Revisa los datos de contacto antes de confirmar.")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                "nombre_tutor": request.user.nombre_completo,
                "email": request.user.email,
                "telefono": request.user.telefono,
            }
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "pedidos/checkout.html",
        {
            "form": form,
            "items": items,
            "totales": calcular_totales(items),
        },
    )


def comprobante(request):
    """Muestra el comprobante generado y almacenado en la sesión."""
    datos = request.session.get(CLAVE_COMPROBANTE)
    if not datos:
        messages.info(request, "No hay un comprobante reciente para mostrar.")
        return redirect("pedidos:ver_canasta")
    return render(request, "pedidos/comprobante.html", {"comprobante": datos})


@require_POST
def cerrar_comprobante(request):
    """Elimina el comprobante de la sesión y vuelve al inicio."""
    request.session.pop(CLAVE_COMPROBANTE, None)
    request.session.modified = True
    messages.info(request, "Comprobante cerrado. ¡Gracias por preferir VetCare Central!")
    return redirect("core:inicio")
