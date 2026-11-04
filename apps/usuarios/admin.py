"""Administración de usuarios institucionales."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = (
        "username",
        "nombre_completo",
        "rut",
        "email",
        "rol",
        "is_staff",
        "is_active",
    )
    list_filter = ("rol", "is_staff", "is_active")
    search_fields = ("username", "first_name", "last_name", "email", "rut")
    list_editable = ("rol", "is_staff", "is_active")
    readonly_fields = ("creado_en", "last_login", "date_joined")
    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Datos institucionales VetCare",
            {"fields": ("rut", "telefono", "rol", "creado_en")},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Datos institucionales VetCare",
            {"fields": ("first_name", "last_name", "email", "rut", "telefono", "rol")},
        ),
    )

    @admin.display(description="Nombre completo", ordering="first_name")
    def nombre_completo(self, obj):
        return obj.nombre_completo
