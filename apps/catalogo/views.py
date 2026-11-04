"""Vistas del catálogo: lectura pública y CRUD protegido para staff."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import ProductoForm
from .models import CategoriaProducto, Producto

ORDENES = {
    "nombre_asc": ("nombre", "Nombre A-Z"),
    "nombre_desc": ("-nombre", "Nombre Z-A"),
    "precio_asc": ("precio", "Precio: menor a mayor"),
    "precio_desc": ("-precio", "Precio: mayor a menor"),
    "recientes": ("-creado_en", "Más recientes"),
}
ITEMS_POR_PAGINA = 6

staff_requerido = user_passes_test(lambda u: u.is_staff, login_url="/usuarios/login/")


def lista(request):
    """Catálogo público con buscador Q, filtros, orden y paginación."""
    productos = Producto.objects.select_related("categoria").filter(
        activo=True, categoria__activo=True
    )

    busqueda = request.GET.get("q", "").strip()
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda)
            | Q(descripcion__icontains=busqueda)
            | Q(codigo__icontains=busqueda)
            | Q(marca__icontains=busqueda)
            | Q(categoria__nombre__icontains=busqueda)
        )

    categoria_slug = request.GET.get("categoria", "").strip()
    if categoria_slug:
        productos = productos.filter(categoria__slug=categoria_slug)

    orden = request.GET.get("orden", "nombre_asc")
    if orden not in ORDENES:
        orden = "nombre_asc"
    productos = productos.order_by(ORDENES[orden][0])

    paginator = Paginator(productos, ITEMS_POR_PAGINA)
    page_obj = paginator.get_page(request.GET.get("page"))

    categorias = (
        CategoriaProducto.objects.filter(activo=True)
        .annotate(
            total_activos=Count(
                "productos",
                filter=Q(productos__activo=True),
                distinct=True,
            )
        )
        .order_by("nombre")
    )

    querystring = request.GET.copy()
    querystring.pop("page", None)

    contexto = {
        "page_obj": page_obj,
        "productos": page_obj.object_list,
        "categorias": categorias,
        "busqueda": busqueda,
        "categoria_actual": categoria_slug,
        "orden_actual": orden,
        "opciones_orden": [(clave, etiqueta) for clave, (_, etiqueta) in ORDENES.items()],
        "total_resultados": paginator.count,
        "querystring": querystring.urlencode(),
    }
    return render(request, "catalogo/lista.html", contexto)


def detalle(request, slug):
    """Detalle individual de un producto por slug."""
    producto = get_object_or_404(
        Producto.objects.select_related("categoria"), slug=slug
    )
    if not producto.activo and not request.user.is_staff:
        raise Http404("El producto no está disponible.")

    relacionados = (
        Producto.objects.filter(
            categoria=producto.categoria,
            activo=True,
            estado=Producto.Estado.DISPONIBLE,
        )
        .exclude(pk=producto.pk)
        .select_related("categoria")[:3]
    )

    return render(
        request,
        "catalogo/detalle.html",
        {"producto": producto, "relacionados": relacionados},
    )


@login_required
@staff_requerido
def crear(request):
    """Crea un producto (solo staff)."""
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(
                request,
                f"El producto «{producto.nombre}» fue creado correctamente.",
            )
            return redirect(producto.get_absolute_url())
        messages.error(request, "Revisa los campos marcados para crear el producto.")
    else:
        form = ProductoForm()

    return render(
        request,
        "catalogo/formulario.html",
        {
            "form": form,
            "titulo": "Nuevo producto",
            "subtitulo": "Registra un producto para la tienda.",
            "accion": "Crear producto",
        },
    )


@login_required
@staff_requerido
def editar(request, slug):
    """Actualiza un producto existente (solo staff)."""
    producto = get_object_or_404(Producto, slug=slug)

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto = form.save()
            messages.success(
                request,
                f"El producto «{producto.nombre}» fue actualizado correctamente.",
            )
            return redirect(producto.get_absolute_url())
        messages.error(request, "Revisa los campos marcados para guardar los cambios.")
    else:
        form = ProductoForm(instance=producto)

    return render(
        request,
        "catalogo/formulario.html",
        {
            "form": form,
            "producto": producto,
            "titulo": f"Editar: {producto.nombre}",
            "subtitulo": f"Código {producto.codigo} · {producto.categoria.nombre}",
            "accion": "Guardar cambios",
        },
    )


@login_required
@staff_requerido
@require_http_methods(["GET", "POST"])
def eliminar(request, slug):
    """Eliminación controlada con confirmación previa (solo staff)."""
    producto = get_object_or_404(Producto, slug=slug)

    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f"El producto «{nombre}» fue eliminado del catálogo.")
        return redirect("catalogo:lista")

    return render(
        request,
        "catalogo/confirmar_eliminacion.html",
        {"producto": producto},
    )
