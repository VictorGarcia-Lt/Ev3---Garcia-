from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import LoginForm

app_name = "usuarios"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="usuarios/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("registro/", views.registro, name="registro"),
    path("perfil/", views.perfil, name="perfil"),
    path(
        "perfil/password/",
        auth_views.PasswordChangeView.as_view(
            template_name="usuarios/password_change_form.html",
            success_url=reverse_lazy("usuarios:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "perfil/password/hecho/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="usuarios/password_change_done.html"
        ),
        name="password_change_done",
    ),
]
