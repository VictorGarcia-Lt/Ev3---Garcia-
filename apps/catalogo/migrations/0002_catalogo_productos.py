"""Migra el catálogo clínico a un catálogo de productos de pet shop.

La migración conserva los productos existentes, elimina los registros de
servicios y transforma las categorías antiguas en las categorías de la tienda.
"""
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def migrar_datos(apps, schema_editor):
    Categoria = apps.get_model("catalogo", "EspecialidadServicio")
    Producto = apps.get_model("catalogo", "PrestacionProducto")

    # Una base nueva no tiene datos que transformar; las categorías de la
    # tienda se crean con ``poblar_datos``.
    if not Categoria.objects.exists() and not Producto.objects.exists():
        return

    # Los servicios clínicos, de estética y sus profesionales dejan de existir.
    Producto.objects.filter(tipo="SERVICIO").delete()

    if not Producto.objects.exists():
        Categoria.objects.all().delete()
        return

    # La categoría mixta antigua se transforma en la categoría de alimentos.
    categoria_alimentos = Categoria.objects.filter(slug="farmacia-alimentos").first()
    if categoria_alimentos is None:
        categoria_alimentos = Categoria.objects.filter(slug="alimentos-nutricion").first()
    if categoria_alimentos is None:
        categoria_alimentos = Categoria.objects.create(
            nombre="Alimentos y Nutrición",
            slug="alimentos-nutricion",
            descripcion="Alimentos balanceados, snacks y premios para mascotas.",
        )
    else:
        categoria_alimentos.nombre = "Alimentos y Nutrición"
        categoria_alimentos.slug = "alimentos-nutricion"
        categoria_alimentos.descripcion = (
            "Alimentos balanceados, snacks y premios para mascotas."
        )
        categoria_alimentos.activo = True
        categoria_alimentos.save()

    # Cualquier producto que quedara en una categoría de servicios se mueve a
    # una categoría de productos antes de eliminar las categorías antiguas.
    Producto.objects.exclude(especialidad_id=categoria_alimentos.pk).update(
        especialidad_id=categoria_alimentos.pk
    )
    Categoria.objects.exclude(pk=categoria_alimentos.pk).delete()

    # El stock de servicios ya no se usa; los productos sin stock pasan a 0.
    Producto.objects.filter(stock__isnull=True).update(
        stock=0,
        estado="AGOTADO",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(migrar_datos, migrations.RunPython.noop),
        migrations.RenameModel(
            old_name="EspecialidadServicio",
            new_name="CategoriaProducto",
        ),
        migrations.RenameModel(
            old_name="PrestacionProducto",
            new_name="Producto",
        ),
        migrations.RenameField(
            model_name="producto",
            old_name="especialidad",
            new_name="categoria",
        ),
        migrations.RemoveIndex(
            model_name="producto",
            name="catalogo_pr_tipo_4c896e_idx",
        ),
        migrations.RemoveField(
            model_name="producto",
            name="tipo",
        ),
        migrations.RemoveField(
            model_name="producto",
            name="profesional",
        ),
        migrations.RemoveField(
            model_name="producto",
            name="duracion_minutos",
        ),
        migrations.AlterField(
            model_name="categoriaproducto",
            name="activo",
            field=models.BooleanField(default=True, verbose_name="Activa"),
        ),
        migrations.AlterField(
            model_name="categoriaproducto",
            name="creado_en",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Creada en"),
        ),
        migrations.AlterField(
            model_name="categoriaproducto",
            name="descripcion",
            field=models.TextField(
                blank=True,
                help_text="Describe brevemente los productos de esta categoría.",
                verbose_name="Descripción",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="activo",
            field=models.BooleanField(
                default=True,
                help_text="Desmarca para ocultar el producto sin eliminar el registro.",
                verbose_name="Activo",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="categoria",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="productos",
                to="catalogo.categoriaproducto",
                verbose_name="Categoría",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="codigo",
            field=models.CharField(
                help_text="Código alfanumérico único (ej: ALI-001, ACC-015).",
                max_length=20,
                unique=True,
                verbose_name="Código",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="estado",
            field=models.CharField(
                choices=[
                    ("DISPONIBLE", "Disponible"),
                    ("SUSPENDIDO", "Suspendido temporalmente"),
                    ("AGOTADO", "Agotado"),
                ],
                default="DISPONIBLE",
                max_length=12,
                verbose_name="Estado",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="imagen",
            field=models.ImageField(
                blank=True,
                help_text="Foto del producto.",
                null=True,
                upload_to="catalogo/",
                verbose_name="Imagen",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="marca",
            field=models.CharField(
                blank=True,
                help_text="Marca o fabricante del producto.",
                max_length=100,
                verbose_name="Marca",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="precio",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Monto en pesos chilenos. Debe ser mayor que cero.",
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
                verbose_name="Precio de venta (CLP)",
            ),
        ),
        migrations.AlterField(
            model_name="producto",
            name="stock",
            field=models.PositiveIntegerField(
                help_text="Unidades disponibles para la venta. Puede ser 0.",
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="Stock disponible",
            ),
        ),
        migrations.AlterModelOptions(
            name="categoriaproducto",
            options={
                "ordering": ["nombre"],
                "verbose_name": "Categoría de producto",
                "verbose_name_plural": "Categorías de producto",
            },
        ),
        migrations.AlterModelOptions(
            name="producto",
            options={
                "ordering": ["nombre"],
                "verbose_name": "Producto",
                "verbose_name_plural": "Productos",
                "indexes": [
                    models.Index(
                        fields=["estado", "activo"],
                        name="catalogo_pr_estado_43ed2b_idx",
                    )
                ],
            },
        ),
    ]
