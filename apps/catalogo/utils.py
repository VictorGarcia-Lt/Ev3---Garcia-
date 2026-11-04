"""Utilidades compartidas del catálogo."""
from django.utils.text import slugify


def generar_slug_unico(modelo, texto, pk=None):
    """Genera un slug único para el modelo indicado."""
    base = slugify(texto)[:110] or "registro"
    queryset = modelo.objects.all()
    if pk is not None:
        queryset = queryset.exclude(pk=pk)

    candidato = base
    contador = 2
    while queryset.filter(slug=candidato).exists():
        candidato = f"{base}-{contador}"
        contador += 1
    return candidato
