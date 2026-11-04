"""Modelo de usuario institucional de VetCare Central."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse

from .validators import formatear_rut, normalizar_rut, validar_rut


class Usuario(AbstractUser):
    """Usuario extendido con RUT, teléfono y rol institucional."""

    class Rol(models.TextChoices):
        CLIENTE = "CLIENTE", "Cliente"
        VENDEDOR = "VENDEDOR", "Vendedor / Staff"
        ADMINISTRATIVO = "ADMINISTRATIVO", "Administrativo"

    rut = models.CharField(
        "RUT",
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        validators=[validar_rut],
        help_text="Formato 12.345.678-5. El dígito verificador se valida automáticamente.",
    )
    telefono = models.CharField(
        "Teléfono",
        max_length=20,
        blank=True,
        help_text="Ej: +56 9 1234 5678",
    )
    rol = models.CharField(
        "Rol institucional",
        max_length=20,
        choices=Rol.choices,
        default=Rol.CLIENTE,
    )
    creado_en = models.DateTimeField("Fecha de registro", auto_now_add=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["first_name", "last_name", "username"]

    def __str__(self):
        return self.nombre_completo

    def save(self, *args, **kwargs):
        if self.rut:
            self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)

    @property
    def nombre_completo(self):
        nombre = f"{self.first_name} {self.last_name}".strip()
        return nombre or self.username

    @property
    def rut_formateado(self):
        return formatear_rut(self.rut) if self.rut else "—"

    def get_absolute_url(self):
        return reverse("usuarios:perfil")
