"""Backend de autenticación: permite ingresar con usuario o correo."""
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import Usuario


class UsuarioBackend(ModelBackend):
    """Autentica por nombre de usuario o correo electrónico."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(Usuario.USERNAME_FIELD)
        if username is None or password is None:
            return None

        filtro = Q(username__iexact=username) | Q(email__iexact=username)
        usuario = Usuario.objects.filter(filtro).order_by("id").first()

        if usuario is None:
            Usuario().set_password(password)
            return None

        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
