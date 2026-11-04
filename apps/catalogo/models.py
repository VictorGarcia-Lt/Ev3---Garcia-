"""Modelos de categorías y productos de la tienda."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from .utils import generar_slug_unico


class CategoriaProducto(models.Model):
    """Categoría que agrupa los productos de la tienda."""

    nombre = models.CharField("Nombre", max_length=100, unique=True)
    slug = models.SlugField(
        "Slug",
        max_length=120,
        unique=True,
        blank=True,
        help_text="Se genera automáticamente a partir del nombre.",
    )
    descripcion = models.TextField(
        "Descripción",
        blank=True,
        help_text="Describe brevemente los productos de esta categoría.",
    )
    activo = models.BooleanField("Activa", default=True)
    creado_en = models.DateTimeField("Creada en", auto_now_add=True)

    class Meta:
        verbose_name = "Categoría de producto"
        verbose_name_plural = "Categorías de producto"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generar_slug_unico(CategoriaProducto, self.nombre, self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{reverse('catalogo:lista')}?categoria={self.slug}"

    @property
    def total_productos(self):
        return self.productos.filter(activo=True).count()


class Producto(models.Model):
    """Producto de pet shop disponible para venta en línea."""

    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        SUSPENDIDO = "SUSPENDIDO", "Suspendido temporalmente"
        AGOTADO = "AGOTADO", "Agotado"

    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="Categoría",
    )
    codigo = models.CharField(
        "Código",
        max_length=20,
        unique=True,
        help_text="Código alfanumérico único (ej: ALI-001, ACC-015).",
    )
    nombre = models.CharField("Nombre", max_length=150)
    slug = models.SlugField(
        "Slug",
        max_length=170,
        unique=True,
        blank=True,
        help_text="Identificador para la URL de detalle; se genera automáticamente.",
    )
    descripcion = models.TextField("Descripción")
    marca = models.CharField(
        "Marca",
        max_length=100,
        blank=True,
        help_text="Marca o fabricante del producto.",
    )
    precio = models.DecimalField(
        "Precio de venta (CLP)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Monto en pesos chilenos. Debe ser mayor que cero.",
    )
    stock = models.PositiveIntegerField(
        "Stock disponible",
        validators=[MinValueValidator(0)],
        help_text="Unidades disponibles para la venta. Puede ser 0.",
    )
    estado = models.CharField(
        "Estado",
        max_length=12,
        choices=Estado.choices,
        default=Estado.DISPONIBLE,
    )
    imagen = models.ImageField(
        "Imagen",
        upload_to="catalogo/",
        blank=True,
        null=True,
        help_text="Foto del producto.",
    )
    activo = models.BooleanField(
        "Activo",
        default=True,
        help_text="Desmarca para ocultar el producto sin eliminar el registro.",
    )
    creado_en = models.DateTimeField("Creado en", auto_now_add=True)
    actualizado_en = models.DateTimeField("Actualizado en", auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]
        indexes = [
            models.Index(
                fields=["estado", "activo"],
                name="catalogo_pr_estado_43ed2b_idx",
            ),
        ]

    def __str__(self):
        return f"{self.codigo} · {self.nombre}"

    def save(self, *args, **kwargs):
        self.codigo = (self.codigo or "").strip().upper()
        if not self.slug:
            self.slug = generar_slug_unico(Producto, self.nombre, self.pk)
        super().save(*args, **kwargs)

    def clean(self):
        """Valida precio, stock y coherencia del estado operativo."""
        errores = {}

        if self.precio is not None and self.precio <= Decimal("0"):
            errores["precio"] = "El precio debe ser mayor que cero."

        if self.stock is None:
            errores["stock"] = "Debes indicar el stock del producto."
        elif self.stock == 0 and self.estado == self.Estado.DISPONIBLE:
            errores["estado"] = (
                "Un producto sin stock no puede estar en estado Disponible."
            )

        if errores:
            raise ValidationError(errores)

    @property
    def disponible(self):
        """Determina si el producto se puede comprar en este momento."""
        if not self.activo or not self.categoria.activo:
            return False
        if self.estado != self.Estado.DISPONIBLE:
            return False
        return (self.stock or 0) > 0

    @property
    def clase_estado(self):
        """Clase Bootstrap asociada al estado operativo."""
        return {
            self.Estado.DISPONIBLE: "success",
            self.Estado.SUSPENDIDO: "warning",
            self.Estado.AGOTADO: "danger",
        }.get(self.estado, "secondary")

    def get_absolute_url(self):
        return reverse("catalogo:detalle", kwargs={"slug": self.slug})
