"""Validadores y utilidades para el RUT chileno."""
import re

from django.core.exceptions import ValidationError


def normalizar_rut(valor):
    """Deja el RUT en formato 12345678-9 (sin puntos y con guion)."""
    if not valor:
        return ""
    limpio = re.sub(r"[.\s]", "", str(valor)).upper()
    if "-" not in limpio and len(limpio) > 1:
        limpio = f"{limpio[:-1]}-{limpio[-1]}"
    return limpio


def formatear_rut(valor):
    """Devuelve el RUT con puntos: 12.345.678-5."""
    limpio = normalizar_rut(valor)
    if not limpio or "-" not in limpio:
        return limpio
    cuerpo, dv = limpio.split("-", 1)
    if not cuerpo.isdigit():
        return limpio
    return f"{int(cuerpo):,}".replace(",", ".") + f"-{dv}"


def validar_rut(valor):
    """Valida el dígito verificador del RUT mediante módulo 11."""
    rut = normalizar_rut(valor)
    if not re.fullmatch(r"\d{7,8}-[\dK]", rut):
        raise ValidationError(
            "Ingresa un RUT válido con su dígito verificador (ej: 12.345.678-5).",
            code="rut_invalido",
        )

    cuerpo, dv = rut.split("-")
    suma = 0
    multiplicador = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1

    resto = 11 - (suma % 11)
    esperado = "0" if resto == 11 else "K" if resto == 10 else str(resto)

    if dv != esperado:
        raise ValidationError(
            "El RUT ingresado no es válido (dígito verificador incorrecto).",
            code="rut_invalido",
        )
