"""Context processor: contador global de la canasta para el navbar."""
from .carrito import contar_unidades


def canasta_global(request):
    """Inyecta el total de unidades de la canasta en todas las plantillas."""
    try:
        total = contar_unidades(request.session)
    except Exception:  # pragma: no cover
        total = 0
    return {"canasta_total_items": total}
