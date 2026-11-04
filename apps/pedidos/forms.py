"""Formulario de checkout para la compra de productos."""
from django import forms

from apps.usuarios.forms import EstiloBootstrapMixin


class CheckoutForm(EstiloBootstrapMixin, forms.Form):
    """Datos de contacto y entrega para generar el comprobante de compra."""

    nombre_tutor = forms.CharField(
        label="Nombre del cliente",
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Camila Rojas"}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "cliente@correo.cl"}),
    )
    telefono = forms.CharField(
        label="Teléfono de contacto",
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "+56 9 1234 5678"}),
    )
    direccion = forms.CharField(
        label="Dirección de entrega",
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Av. Los Robles 1240, Santiago (opcional)"}
        ),
        help_text="Opcional. Si la dejas vacía, coordinaremos el retiro en tienda.",
    )
    observaciones = forms.CharField(
        label="Observaciones de la compra",
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 3, "placeholder": "Indicaciones para la entrega o comentarios."}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_estilos()

    def clean_telefono(self):
        telefono = self.cleaned_data["telefono"].strip()
        if len(telefono) < 8:
            raise forms.ValidationError("Ingresa un teléfono de contacto válido.")
        return telefono
