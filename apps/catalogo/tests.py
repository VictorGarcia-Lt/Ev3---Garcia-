"""Pruebas del catálogo público y del CRUD protegido."""
import io
import tempfile
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .forms import ProductoForm
from .models import CategoriaProducto, Producto

Usuario = get_user_model()


class BaseCatalogoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alimentos = CategoriaProducto.objects.create(
            nombre="Alimentos y Nutrición",
            descripcion="Alimentos balanceados y snacks.",
        )
        cls.higiene = CategoriaProducto.objects.create(
            nombre="Higiene y Estética",
            descripcion="Shampoos y cepillos.",
        )
        cls.producto = Producto.objects.create(
            categoria=cls.alimentos,
            codigo="ALI-001",
            nombre="Alimento premium perro adulto",
            descripcion="Alimento balanceado para perros adultos.",
            marca="NutriCan",
            precio="34990",
            stock=10,
        )
        cls.agotado = Producto.objects.create(
            categoria=cls.alimentos,
            codigo="ALI-002",
            nombre="Snacks dentales",
            descripcion="Snacks para higiene dental.",
            marca="DentalPet",
            precio="5990",
            stock=0,
            estado=Producto.Estado.AGOTADO,
        )
        cls.inactivo = Producto.objects.create(
            categoria=cls.higiene,
            codigo="HIG-099",
            nombre="Producto descontinuado",
            descripcion="No debe aparecer en el catálogo público.",
            marca="PetCare",
            precio="10000",
            stock=5,
            activo=False,
        )

    def setUp(self):
        self.staff = Usuario.objects.create_user(
            username="staff",
            password="ClaveSegura123",
            email="staff@vetcare.cl",
            is_staff=True,
        )
        self.cliente = Usuario.objects.create_user(
            username="cliente",
            password="ClaveSegura123",
            email="cliente@vetcare.cl",
        )


class CatalogoPublicoTests(BaseCatalogoTests):
    def test_lista_muestra_solo_activos(self):
        respuesta = self.client.get(reverse("catalogo:lista"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Alimento premium perro adulto")
        self.assertContains(respuesta, "Snacks dentales")
        self.assertNotContains(respuesta, "Producto descontinuado")
        self.assertEqual(respuesta.context["total_resultados"], 2)

    def test_busqueda_multicampo_q(self):
        for termino in ("NutriCan", "balanceado", "ALI-001", "Alimentos"):
            respuesta = self.client.get(reverse("catalogo:lista"), {"q": termino})
            self.assertEqual(respuesta.status_code, 200, termino)
            self.assertGreaterEqual(
                respuesta.context["total_resultados"],
                1,
                f"Sin resultados para {termino}",
            )

    def test_filtro_por_categoria(self):
        respuesta = self.client.get(
            reverse("catalogo:lista"), {"categoria": self.alimentos.slug}
        )
        self.assertEqual(respuesta.context["total_resultados"], 2)
        self.assertContains(respuesta, "Alimento premium perro adulto")
        self.assertNotContains(respuesta, "Producto descontinuado")

    def test_ordenamiento_por_precio(self):
        respuesta = self.client.get(reverse("catalogo:lista"), {"orden": "precio_asc"})
        precios = [p.precio for p in respuesta.context["productos"]]
        self.assertEqual(precios, sorted(precios))

        respuesta = self.client.get(reverse("catalogo:lista"), {"orden": "precio_desc"})
        precios = [p.precio for p in respuesta.context["productos"]]
        self.assertEqual(precios, sorted(precios, reverse=True))

    def test_paginacion(self):
        for indice in range(8):
            Producto.objects.create(
                categoria=self.alimentos,
                codigo=f"PAG-{indice:03d}",
                nombre=f"Producto paginado {indice}",
                descripcion="Registro de prueba para paginación.",
                marca="Test",
                precio="5000",
                stock=3,
            )
        respuesta = self.client.get(reverse("catalogo:lista"))
        self.assertEqual(len(respuesta.context["productos"]), 6)
        self.assertTrue(respuesta.context["page_obj"].has_next())

        respuesta = self.client.get(reverse("catalogo:lista"), {"page": 2})
        self.assertEqual(respuesta.context["page_obj"].number, 2)
        self.assertEqual(len(respuesta.context["productos"]), 4)

    def test_detalle_por_slug(self):
        respuesta = self.client.get(self.producto.get_absolute_url())
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Alimento premium perro adulto")
        self.assertContains(respuesta, "NutriCan")
        self.assertContains(
            respuesta, reverse("pedidos:agregar", args=[self.producto.pk])
        )

    def test_detalle_inactivo_oculto_para_publico(self):
        respuesta = self.client.get(self.inactivo.get_absolute_url())
        self.assertEqual(respuesta.status_code, 404)

    def test_detalle_inactivo_visible_para_staff(self):
        self.client.force_login(self.staff)
        respuesta = self.client.get(self.inactivo.get_absolute_url())
        self.assertEqual(respuesta.status_code, 200)

    def test_slug_autogenerado(self):
        self.assertEqual(self.producto.slug, "alimento-premium-perro-adulto")

    def test_producto_agotado_no_muestra_formulario_de_compra(self):
        respuesta = self.client.get(self.agotado.get_absolute_url())
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "no está disponible para agregar")
        self.assertNotContains(
            respuesta, reverse("pedidos:agregar", args=[self.agotado.pk])
        )


class CrudProtegidoTests(BaseCatalogoTests):
    def test_anonimo_redirigido_al_login(self):
        respuesta = self.client.get(reverse("catalogo:crear"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("usuarios:login"), respuesta.url)

    def test_cliente_sin_staff_no_puede_crear(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.get(reverse("catalogo:crear"))
        self.assertEqual(respuesta.status_code, 302)

    def test_staff_puede_acceder_al_formulario(self):
        self.client.force_login(self.staff)
        respuesta = self.client.get(reverse("catalogo:crear"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Nuevo producto")

    def test_crear_producto_valido(self):
        self.client.force_login(self.staff)
        respuesta = self.client.post(
            reverse("catalogo:crear"),
            {
                "categoria": self.alimentos.pk,
                "codigo": "ALI-010",
                "nombre": "Alimento para gato adulto",
                "descripcion": "Fórmula balanceada para gatos adultos.",
                "marca": "FelixCan",
                "precio": "19990",
                "stock": "12",
                "estado": "DISPONIBLE",
                "activo": "on",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        creado = Producto.objects.get(codigo="ALI-010")
        self.assertEqual(creado.precio, Decimal("19990"))
        self.assertEqual(creado.slug, "alimento-para-gato-adulto")

    def test_crear_con_imagen_multimedia(self):
        self.client.force_login(self.staff)
        buffer = io.BytesIO()
        Image.new("RGB", (12, 12), color="#0e6b62").save(buffer, format="PNG")
        imagen = SimpleUploadedFile(
            "foto.png", buffer.getvalue(), content_type="image/png"
        )
        with tempfile.TemporaryDirectory() as directorio:
            with self.settings(MEDIA_ROOT=directorio):
                respuesta = self.client.post(
                    reverse("catalogo:crear"),
                    {
                        "categoria": self.alimentos.pk,
                        "codigo": "IMG-001",
                        "nombre": "Producto con imagen",
                        "descripcion": "Registro con archivo multimedia.",
                        "marca": "VetCare",
                        "precio": "9990",
                        "stock": "4",
                        "estado": "DISPONIBLE",
                        "activo": "on",
                        "imagen": imagen,
                    },
                )
                self.assertEqual(respuesta.status_code, 302)
                creado = Producto.objects.get(codigo="IMG-001")
                self.assertTrue(creado.imagen.name.startswith("catalogo/"))

    def test_precio_cero_es_rechazado(self):
        self.client.force_login(self.staff)
        respuesta = self.client.post(
            reverse("catalogo:crear"),
            {
                "categoria": self.alimentos.pk,
                "codigo": "BAD-001",
                "nombre": "Producto inválido",
                "descripcion": "Precio en cero.",
                "marca": "",
                "precio": "0",
                "stock": "1",
                "estado": "DISPONIBLE",
                "activo": "on",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "debe ser mayor que cero")
        self.assertFalse(Producto.objects.filter(codigo="BAD-001").exists())

    def test_producto_sin_stock_es_rechazado(self):
        self.client.force_login(self.staff)
        respuesta = self.client.post(
            reverse("catalogo:crear"),
            {
                "categoria": self.alimentos.pk,
                "codigo": "BAD-002",
                "nombre": "Producto sin stock",
                "descripcion": "Falta stock.",
                "marca": "",
                "precio": "5000",
                "stock": "",
                "estado": "DISPONIBLE",
                "activo": "on",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Indica el stock")
        self.assertFalse(Producto.objects.filter(codigo="BAD-002").exists())

    def test_stock_cero_exige_estado_agotado(self):
        self.client.force_login(self.staff)
        respuesta = self.client.post(
            reverse("catalogo:crear"),
            {
                "categoria": self.alimentos.pk,
                "codigo": "BAD-003",
                "nombre": "Producto sin unidades",
                "descripcion": "Stock en cero.",
                "marca": "",
                "precio": "5000",
                "stock": "0",
                "estado": "DISPONIBLE",
                "activo": "on",
            },
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "cambia el estado a Agotado")
        self.assertFalse(Producto.objects.filter(codigo="BAD-003").exists())

    def test_editar_producto(self):
        self.client.force_login(self.staff)
        respuesta = self.client.post(
            reverse("catalogo:editar", args=[self.producto.slug]),
            {
                "categoria": self.producto.categoria.pk,
                "codigo": self.producto.codigo,
                "nombre": "Alimento premium actualizado",
                "descripcion": self.producto.descripcion,
                "marca": self.producto.marca,
                "precio": "36990",
                "stock": "8",
                "estado": "DISPONIBLE",
                "activo": "on",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.nombre, "Alimento premium actualizado")
        self.assertEqual(self.producto.precio, Decimal("36990"))

    def test_eliminar_producto_con_confirmacion(self):
        self.client.force_login(self.staff)
        confirmacion = self.client.get(
            reverse("catalogo:eliminar", args=[self.agotado.slug])
        )
        self.assertEqual(confirmacion.status_code, 200)
        self.assertContains(confirmacion, "Confirmar eliminación")

        respuesta = self.client.post(
            reverse("catalogo:eliminar", args=[self.agotado.slug])
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(Producto.objects.filter(pk=self.agotado.pk).exists())

    def test_cliente_no_puede_eliminar(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.post(
            reverse("catalogo:eliminar", args=[self.producto.slug])
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Producto.objects.filter(pk=self.producto.pk).exists())


class FormularioTests(BaseCatalogoTests):
    def test_clean_precio_negativo(self):
        form = ProductoForm(
            data={
                "categoria": self.alimentos.pk,
                "codigo": "NEG-001",
                "nombre": "Precio negativo",
                "descripcion": "Prueba.",
                "marca": "Test",
                "precio": "-100",
                "stock": "1",
                "estado": "DISPONIBLE",
                "activo": True,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("precio", form.errors)

    def test_codigo_alfanumerico(self):
        form = ProductoForm(
            data={
                "categoria": self.alimentos.pk,
                "codigo": "código inválido",
                "nombre": "Código inválido",
                "descripcion": "Prueba.",
                "marca": "Test",
                "precio": "1000",
                "stock": "1",
                "estado": "DISPONIBLE",
                "activo": True,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("codigo", form.errors)
