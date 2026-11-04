"""Formularios de registro, login y perfil de usuario."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Usuario
from .validators import normalizar_rut


class EstiloBootstrapMixin:
    """Aplica clases de Bootstrap 5 a todos los widgets del formulario."""

    def _aplicar_estilos(self):
        for nombre, campo in self.fields.items():
            widget = campo.widget
            if isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
            if campo.required and not isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("required", "required")


class RegistroForm(EstiloBootstrapMixin, UserCreationForm):
    """Registro público de clientes con RUT y teléfono."""

    email = forms.EmailField(
        label="Correo electrónico",
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "cliente@correo.cl"}),
    )
    rut = forms.CharField(
        label="RUT",
        max_length=12,
        help_text="Ej: 19.876.543-0",
        widget=forms.TextInput(attrs={"placeholder": "19.876.543-0"}),
    )
    telefono = forms.CharField(
        label="Teléfono",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "+56 9 1234 5678"}),
    )

    class Meta:
        model = Usuario
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "rut",
            "telefono",
        )
        labels = {
            "username": "Nombre de usuario",
            "first_name": "Nombres",
            "last_name": "Apellidos",
        }
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "cliente.vetcare"}),
            "first_name": forms.TextInput(attrs={"placeholder": "Camila"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Rojas"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["password1"].label = "Contraseña"
        self.fields["password2"].label = "Confirmar contraseña"
        self._aplicar_estilos()

    def save(self, commit=True):
        """El registro público siempre crea una cuenta de cliente."""
        usuario = super().save(commit=False)
        usuario.rol = Usuario.Rol.CLIENTE
        if commit:
            usuario.save()
        return usuario

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta registrada con este correo.")
        return email

    def clean_rut(self):
        rut = normalizar_rut(self.cleaned_data["rut"])
        if Usuario.objects.filter(rut=rut).exists():
            raise forms.ValidationError("Ya existe un usuario registrado con este RUT.")
        return rut


class PerfilForm(EstiloBootstrapMixin, forms.ModelForm):
    """Edición de los datos personales del usuario autenticado."""

    class Meta:
        model = Usuario
        fields = ("first_name", "last_name", "email", "telefono")
        labels = {
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
            "telefono": "Teléfono",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_estilos()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        existe = (
            Usuario.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        )
        if existe:
            raise forms.ValidationError("Ese correo ya está asociado a otra cuenta.")
        return email


class LoginForm(EstiloBootstrapMixin, AuthenticationForm):
    """Formulario de inicio de sesión con estilos Bootstrap."""

    username = forms.CharField(
        label="Usuario o correo",
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "admin"}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_estilos()
