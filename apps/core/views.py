"""Vistas institucionales de VetCare Central."""
from django.db.models import Count, Q
from django.shortcuts import render

from apps.catalogo.models import CategoriaProducto, Producto


def inicio(request):
    """Página de inicio con categorías y productos destacados."""
    categorias = (
        CategoriaProducto.objects.filter(activo=True)
        .annotate(
            total_activos=Count(
                "productos",
                filter=Q(productos__activo=True),
                distinct=True,
            )
        )
        .order_by("nombre")[:4]
    )
    productos_destacados = (
        Producto.objects.filter(
            activo=True,
            estado=Producto.Estado.DISPONIBLE,
            categoria__activo=True,
        )
        .select_related("categoria")
        .order_by("-creado_en")[:6]
    )
    contexto = {
        "categorias": categorias,
        "productos_destacados": productos_destacados,
        "total_productos": Producto.objects.filter(
            activo=True, categoria__activo=True
        ).count(),
    }
    return render(request, "core/inicio.html", contexto)


def nosotros(request):
    """Página Quiénes Somos de la tienda."""
    categorias = CategoriaProducto.objects.filter(activo=True).order_by("nombre")
    return render(request, "core/nosotros.html", {"categorias": categorias})


def contacto(request):
    """Página de contacto y horarios de la tienda."""
    return render(request, "core/contacto.html")
