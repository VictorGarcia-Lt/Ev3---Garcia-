"""Filtros de plantilla reutilizables para VetCare Central."""
from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def clp(valor):
    """Formatea un monto como peso chileno: 12990 -> $12.990."""
    try:
        monto = int(Decimal(str(valor)))
    except (InvalidOperation, TypeError, ValueError):
        return "$0"
    return "${:,.0f}".format(monto).replace(",", ".")
