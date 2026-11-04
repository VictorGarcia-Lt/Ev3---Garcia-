"""Pruebas de registro, autenticación y perfil."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .validators import validar_rut
from django.core.exceptions import ValidationError

Usuario = get_user_model()


class RegistroTests(TestCase):
    datos_validos = {
        "username": "nuevo.cliente",
        "first_name": "Camila",
        "last_name": "Rojas",
        "email": "camila@correo.cl",
        "rut": "19.876.543-0",
        "telefono": "+56 9 1234 5678",
        "password1": "ClaveMuySegura123",
        "password2": "ClaveMuySegura123",
    }

    def test_registro_crea_usuario_y_autentica(self):
        respuesta = self.client.post(reverse("usuarios:registro"), self.datos_validos)
        self.assertRedirects(respuesta, reverse("usuarios:perfil"))

        usuario = Usuario.objects.get(username="nuevo.cliente")
        self.assertEqual(usuario.email, "camila@correo.cl")
        self.assertEqual(usuario.rut, "19876543-0")
        self.assertEqual(usuario.rol, "CLIENTE")
        self.assertTrue(respuesta.wsgi_request.user.is_authenticated)

    def test_registro_publico_ignora_rol_institucional(self):
        datos = {**self.datos_validos, "rol": "ADMINISTRATIVO"}
        respuesta = self.client.post(reverse("usuarios:registro"), datos)
        self.assertRedirects(respuesta, reverse("usuarios:perfil"))

        usuario = Usuario.objects.get(username="nuevo.cliente")
        self.assertEqual(usuario.rol, "CLIENTE")
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)

    def test_rut_invalido_es_rechazado(self):
        datos = {**self.datos_validos, "rut": "12.345.678-1"}
        respuesta = self.client.post(reverse("usuarios:registro"), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "dígito verificador incorrecto")
        self.assertFalse(Usuario.objects.filter(username="nuevo.cliente").exists())

    def test_email_duplicado_es_rechazado(self):
        Usuario.objects.create_user(
            username="existente", email="camila@correo.cl", password="ClaveSegura123"
        )
        respuesta = self.client.post(reverse("usuarios:registro"), self.datos_validos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ya existe una cuenta registrada con este correo")

    def test_rut_duplicado_es_rechazado(self):
        Usuario.objects.create_user(
            username="existente",
            email="otro@correo.cl",
            password="ClaveSegura123",
            rut="19876543-0",
        )
        respuesta = self.client.post(reverse("usuarios:registro"), self.datos_validos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ya existe un usuario registrado con este RUT")


class RolesTests(TestCase):
    def test_roles_del_pet_shop(self):
        roles = dict(Usuario.Rol.choices)
        self.assertIn("CLIENTE", roles)
        self.assertIn("VENDEDOR", roles)
        self.assertIn("ADMINISTRATIVO", roles)
        self.assertNotIn("VETERINARIO", roles)


class ValidarRutTests(TestCase):
    def test_ruts_validos(self):
        for rut in ("12.345.678-5", "19.876.543-0", "7.654.321-6"):
            validar_rut(rut)

    def test_ruts_invalidos(self):
        for rut in ("12.345.678-1", "abc", "123", ""):
            with self.assertRaises(ValidationError):
                validar_rut(rut)


class PerfilTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(
            username="tutor",
            password="ClaveSegura123",
            first_name="Ana",
            last_name="Pérez",
            email="ana@correo.cl",
            rut="12345678-5",
            telefono="+56 9 1111 2222",
        )

    def test_perfil_requiere_login(self):
        respuesta = self.client.get(reverse("usuarios:perfil"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("usuarios:login"), respuesta.url)

    def test_perfil_muestra_datos(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse("usuarios:perfil"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Ana Pérez")
        self.assertContains(respuesta, "12.345.678-5")

    def test_actualizar_perfil(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(
            reverse("usuarios:perfil"),
            {
                "first_name": "Ana María",
                "last_name": "Pérez Soto",
                "email": "ana.nueva@correo.cl",
                "telefono": "+56 9 3333 4444",
            },
        )
        self.assertRedirects(respuesta, reverse("usuarios:perfil"))
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, "Ana María")
        self.assertEqual(self.usuario.email, "ana.nueva@correo.cl")

    def test_login_con_credenciales(self):
        respuesta = self.client.post(
            reverse("usuarios:login"),
            {"username": "tutor", "password": "ClaveSegura123"},
        )
        self.assertRedirects(respuesta, reverse("usuarios:perfil"))

    def test_login_con_correo_electronico(self):
        respuesta = self.client.post(
            reverse("usuarios:login"),
            {"username": "ana@correo.cl", "password": "ClaveSegura123"},
        )
        self.assertRedirects(respuesta, reverse("usuarios:perfil"))
        self.assertTrue(respuesta.wsgi_request.user.is_authenticated)

    def test_login_con_password_incorrecta(self):
        respuesta = self.client.post(
            reverse("usuarios:login"),
            {"username": "ana@correo.cl", "password": "NoEsLaClave123"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.wsgi_request.user.is_authenticated)


class CambioPasswordTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(
            username="tutor.clave",
            password="ClaveSegura123",
            email="clave@correo.cl",
        )

    def test_cambio_password_requiere_login(self):
        respuesta = self.client.get(reverse("usuarios:password_change"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("usuarios:login"), respuesta.url)

    def test_formulario_cambio_password_se_renderiza(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse("usuarios:password_change"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Cambiar contraseña")

    def test_cambio_password_exitoso(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(
            reverse("usuarios:password_change"),
            {
                "old_password": "ClaveSegura123",
                "new_password1": "NuevaClaveMuySegura456",
                "new_password2": "NuevaClaveMuySegura456",
            },
        )
        self.assertRedirects(respuesta, reverse("usuarios:password_change_done"))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("NuevaClaveMuySegura456"))
        self.assertFalse(self.usuario.check_password("ClaveSegura123"))
