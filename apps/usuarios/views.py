"""Vistas de autenticación y perfil de VetCare Central."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import PerfilForm, RegistroForm


def registro(request):
    """Crea una cuenta y autentica al usuario inmediatamente."""
    if request.user.is_authenticated:
        messages.info(request, "Ya tienes una sesión activa en VetCare Central.")
        return redirect("usuarios:perfil")

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(
                request,
                f"¡Bienvenido/a a VetCare Central, {usuario.nombre_completo}! "
                "Tu cuenta fue creada correctamente.",
            )
            return redirect("usuarios:perfil")
        messages.error(request, "Revisa los datos del formulario e inténtalo nuevamente.")
    else:
        form = RegistroForm()

    return render(request, "usuarios/registro.html", {"form": form})


@login_required
def perfil(request):
    """Muestra y actualiza los datos del usuario autenticado."""
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos personales fueron actualizados.")
            return redirect("usuarios:perfil")
        messages.error(request, "No fue posible guardar los cambios. Revisa el formulario.")
    else:
        form = PerfilForm(instance=request.user)

    return render(request, "usuarios/perfil.html", {"form": form})
