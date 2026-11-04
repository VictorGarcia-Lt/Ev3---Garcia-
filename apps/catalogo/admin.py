"""Panel de administración de categorías y productos."""
from django.contrib import admin, messages

from .models import CategoriaProducto, Producto

admin.site.site_header = "VetCare Central - Panel de Control"
admin.site.site_title = "VetCare Admin"
admin.site.index_title = "Gestión de productos para mascotas"


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "total_productos", "activo", "creado_en")
    list_filter = ("activo", "creado_en")
    search_fields = ("nombre", "descripcion")
    list_editable = ("activo",)
    readonly_fields = ("slug", "creado_en")
    list_per_page = 20
    ordering = ("nombre",)

    fieldsets = (
        ("Identificación", {"fields": ("nombre", "slug")}),
        ("Descripción", {"fields": ("descripcion",)}),
        ("Vigencia", {"fields": ("activo",)}),
        ("Auditoría", {"fields": ("creado_en",), "classes": ("collapse",)}),
    )

    @admin.display(description="N° productos")
    def total_productos(self, obj):
        return obj.productos.filter(activo=True).count()


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "categoria",
        "precio",
        "stock",
        "estado",
        "activo",
    )
    list_filter = ("categoria", "estado", "activo")
    search_fields = ("codigo", "nombre", "descripcion", "marca")
    list_editable = ("precio", "estado", "activo")
    readonly_fields = ("slug", "creado_en", "actualizado_en")
    list_per_page = 15
    list_select_related = ("categoria",)
    save_on_top = True
    ordering = ("categoria", "nombre")
    actions = ("marcar_agotado", "marcar_suspendido", "reactivar")

    fieldsets = (
        (
            "Identificación",
            {"fields": ("codigo", "nombre", "slug", "categoria")},
        ),
        (
            "Descripción",
            {"fields": ("descripcion", "marca")},
        ),
        (
            "Valores y disponibilidad",
            {"fields": ("precio", "stock", "estado", "activo")},
        ),
        ("Multimedia", {"fields": ("imagen",)}),
        (
            "Auditoría",
            {"fields": ("creado_en", "actualizado_en"), "classes": ("collapse",)},
        ),
    )

    @admin.action(description="Marcar seleccionados como Agotado")
    def marcar_agotado(self, request, queryset):
        actualizados = queryset.update(estado=Producto.Estado.AGOTADO)
        self.message_user(
            request,
            f"{actualizados} producto(s) marcados como Agotado.",
            messages.WARNING,
        )

    @admin.action(description="Marcar seleccionados como Suspendido")
    def marcar_suspendido(self, request, queryset):
        actualizados = queryset.update(estado=Producto.Estado.SUSPENDIDO)
        self.message_user(
            request,
            f"{actualizados} producto(s) marcados como Suspendido temporalmente.",
            messages.WARNING,
        )

    @admin.action(description="Reactivar seleccionados")
    def reactivar(self, request, queryset):
        reactivados = 0
        agotados = 0
        for producto in queryset:
            producto.activo = True
            if producto.stock and producto.stock > 0:
                producto.estado = Producto.Estado.DISPONIBLE
                reactivados += 1
            else:
                producto.estado = Producto.Estado.AGOTADO
                agotados += 1
            producto.save(update_fields=["activo", "estado", "actualizado_en"])

        mensaje = f"{reactivados} producto(s) reactivados como Disponible."
        if agotados:
            mensaje += (
                f" {agotados} producto(s) sin stock quedaron marcados como Agotado."
            )
        self.message_user(request, mensaje, messages.SUCCESS)
