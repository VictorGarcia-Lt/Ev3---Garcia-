"""Formulario de creación y edición de productos."""
import re
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .models import Producto


class ProductoForm(forms.ModelForm):
    """ModelForm con Bootstrap 5 y validaciones de negocio."""

    class Meta:
        model = Producto
        fields = (
            "categoria",
            "codigo",
            "nombre",
            "descripcion",
            "marca",
            "precio",
            "stock",
            "estado",
            "imagen",
            "activo",
        )
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "codigo": forms.TextInput(attrs={"placeholder": "ALI-001"}),
            "nombre": forms.TextInput(
                attrs={"placeholder": "Alimento premium para perro adulto"}
            ),
            "marca": forms.TextInput(attrs={"placeholder": "NutriCan"}),
            "precio": forms.NumberInput(attrs={"step": "1", "min": "1"}),
            "stock": forms.NumberInput(attrs={"min": "0"}),
            "imagen": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
        labels = {
            "codigo": "Código único",
            "precio": "Precio de venta (CLP)",
            "imagen": "Imagen del producto",
            "activo": "Producto activo",
        }
        help_texts = {
            "stock": "Unidades disponibles para la venta. Ingresa 0 si está agotado.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")

        self.fields["categoria"].empty_label = "Selecciona una categoría"
        self.fields["stock"].error_messages["required"] = (
            "Indica el stock disponible para este producto."
        )

    def clean_codigo(self):
        codigo = (self.cleaned_data.get("codigo") or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9\-]{2,19}", codigo):
            raise ValidationError(
                "El código debe ser alfanumérico (3 a 20 caracteres) y puede incluir guiones. "
                "Ej: ALI-001."
            )
        return codigo

    def clean_precio(self):
        precio = self.cleaned_data.get("precio")
        if precio is None:
            raise ValidationError("El precio es obligatorio.")
        if precio <= Decimal("0"):
            raise ValidationError("El precio debe ser mayor que cero.")
        return precio

    def clean_imagen(self):
        imagen = self.cleaned_data.get("imagen")
        if imagen and getattr(imagen, "size", 0) > 2 * 1024 * 1024:
            raise ValidationError("La imagen no puede superar los 2 MB.")
        return imagen

    def clean(self):
        datos = super().clean()
        stock = datos.get("stock")
        estado = datos.get("estado")

        if stock is None:
            self.add_error("stock", "Indica el stock disponible para este producto.")
        elif stock == 0 and estado == Producto.Estado.DISPONIBLE:
            self.add_error(
                "estado",
                "Si el stock es 0, cambia el estado a Agotado.",
            )

        return datos
