"""Pruebas de la canasta de compras, checkout, stock y comprobante."""
import re

from django.test import TestCase
from django.urls import reverse

from apps.catalogo.models import CategoriaProducto, Producto

from .carrito import CLAVE_CANASTA, CLAVE_COMPROBANTE


class CanastaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = CategoriaProducto.objects.create(
            nombre="Alimentos y Nutrición",
            descripcion="Alimentos y snacks para mascotas.",
        )
        cls.producto = Producto.objects.create(
            categoria=cls.categoria,
            codigo="ALI-001",
            nombre="Alimento premium",
            descripcion="Alimento balanceado.",
            marca="NutriCan",
            precio="10000",
            stock=5,
        )
        cls.otro_producto = Producto.objects.create(
            categoria=cls.categoria,
            codigo="ALI-002",
            nombre="Shampoo para mascotas",
            descripcion="Shampoo para pieles sensibles.",
            marca="PetCare",
            precio="5000",
            stock=3,
        )
        cls.agotado = Producto.objects.create(
            categoria=cls.categoria,
            codigo="ALI-003",
            nombre="Snacks agotados",
            descripcion="Sin stock.",
            marca="DentalPet",
            precio="5000",
            stock=0,
            estado=Producto.Estado.AGOTADO,
        )

    def _datos_checkout(self, **cambios):
        datos = {
            "nombre_tutor": "Camila Rojas",
            "email": "camila@correo.cl",
            "telefono": "+56 9 1234 5678",
            "direccion": "Av. Los Robles 1240, Santiago",
            "observaciones": "Entregar en recepción.",
        }
        datos.update(cambios)
        return datos

    def test_agregar_producto_y_contador(self):
        respuesta = self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 2}
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            self.client.session[CLAVE_CANASTA][str(self.producto.pk)]["cantidad"], 2
        )

        inicio = self.client.get(reverse("core:inicio"))
        self.assertEqual(inicio.context["canasta_total_items"], 2)

    def test_agregar_producto_valida_stock(self):
        respuesta = self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 6}
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertNotIn(CLAVE_CANASTA, self.client.session)

    def test_no_permite_agregar_agotado(self):
        respuesta = self.client.post(
            reverse("pedidos:agregar", args=[self.agotado.pk]), {"cantidad": 1}
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertNotIn(CLAVE_CANASTA, self.client.session)

    def test_detalle_producto_muestra_compra(self):
        respuesta = self.client.get(self.producto.get_absolute_url())
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(
            respuesta, reverse("pedidos:agregar", args=[self.producto.pk])
        )

    def test_detalle_agotado_no_muestra_compra(self):
        respuesta = self.client.get(self.agotado.get_absolute_url())
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "no está disponible para agregar")
        self.assertNotContains(
            respuesta, reverse("pedidos:agregar", args=[self.agotado.pk])
        )

    def test_actualizar_cantidad(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 1}
        )
        respuesta = self.client.post(
            reverse("pedidos:actualizar", args=[self.producto.pk]), {"cantidad": 4}
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            self.client.session[CLAVE_CANASTA][str(self.producto.pk)]["cantidad"], 4
        )

    def test_actualizar_sobre_stock_no_modifica(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 1}
        )
        self.client.post(
            reverse("pedidos:actualizar", args=[self.producto.pk]), {"cantidad": 9}
        )
        self.assertEqual(
            self.client.session[CLAVE_CANASTA][str(self.producto.pk)]["cantidad"], 1
        )

    def test_quitar_item(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 1}
        )
        self.client.post(reverse("pedidos:quitar", args=[self.producto.pk]))
        self.assertNotIn(CLAVE_CANASTA, self.client.session)

    def test_vaciar_canasta(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 1}
        )
        self.client.post(
            reverse("pedidos:agregar", args=[self.otro_producto.pk]), {"cantidad": 1}
        )
        self.client.post(reverse("pedidos:vaciar"))
        self.assertNotIn(CLAVE_CANASTA, self.client.session)

    def test_canasta_muestra_desglose(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 2}
        )
        respuesta = self.client.get(reverse("pedidos:ver_canasta"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "$20.000")
        self.assertContains(respuesta, "$3.800")
        self.assertContains(respuesta, "$23.800")

    def test_checkout_descuenta_stock_y_genera_comprobante(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 2}
        )

        respuesta = self.client.post(
            reverse("pedidos:checkout"), self._datos_checkout()
        )
        self.assertRedirects(respuesta, reverse("pedidos:comprobante"))
        self.assertNotIn(CLAVE_CANASTA, self.client.session)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 3)
        self.assertEqual(self.producto.estado, Producto.Estado.DISPONIBLE)

        comprobante = self.client.session[CLAVE_COMPROBANTE]
        self.assertRegex(comprobante["folio"], r"^VET-\d{4}-[A-Z0-9]{4}$")
        self.assertEqual(comprobante["subtotal"], "20000")
        self.assertEqual(comprobante["iva"], "3800")
        self.assertEqual(comprobante["total"], "23800")
        self.assertEqual(len(comprobante["items"]), 1)
        self.assertEqual(comprobante["items"][0]["cantidad"], 2)
        self.assertEqual(
            comprobante["items"][0]["categoria"], "Alimentos y Nutrición"
        )

        pagina = self.client.get(reverse("pedidos:comprobante"))
        self.assertEqual(pagina.status_code, 200)
        self.assertContains(pagina, comprobante["folio"])
        self.assertContains(pagina, "Av. Los Robles 1240")
        self.assertContains(pagina, "$23.800")

    def test_checkout_agota_producto_y_actualiza_estado(self):
        self.producto.stock = 1
        self.producto.save(update_fields=["stock"])
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 1}
        )

        respuesta = self.client.post(
            reverse("pedidos:checkout"), self._datos_checkout()
        )
        self.assertRedirects(respuesta, reverse("pedidos:comprobante"))

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 0)
        self.assertEqual(self.producto.estado, Producto.Estado.AGOTADO)

    def test_checkout_no_descuenta_si_formulario_es_invalido(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 1}
        )
        respuesta = self.client.post(
            reverse("pedidos:checkout"),
            self._datos_checkout(telefono="123"),
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "teléfono de contacto válido")

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)
        self.assertIn(CLAVE_CANASTA, self.client.session)
        self.assertNotIn(CLAVE_COMPROBANTE, self.client.session)

    def test_checkout_no_descuenta_si_producto_se_desactiva(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 2}
        )
        self.producto.activo = False
        self.producto.save(update_fields=["activo"])

        respuesta = self.client.post(
            reverse("pedidos:checkout"), self._datos_checkout()
        )
        self.assertRedirects(respuesta, reverse("pedidos:ver_canasta"))

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)
        self.assertNotIn(CLAVE_COMPROBANTE, self.client.session)

    def test_checkout_con_canasta_vacia_redirige(self):
        respuesta = self.client.get(reverse("pedidos:checkout"))
        self.assertRedirects(respuesta, reverse("pedidos:ver_canasta"))

    def test_checkout_rechaza_producto_inexistente_inyectado_en_sesion(self):
        sesion = self.client.session
        sesion[CLAVE_CANASTA] = {"999999": {"cantidad": 1}}
        sesion.save()

        respuesta = self.client.post(
            reverse("pedidos:checkout"), self._datos_checkout()
        )
        self.assertRedirects(respuesta, reverse("pedidos:ver_canasta"))
        self.assertNotIn(CLAVE_COMPROBANTE, self.client.session)
        self.assertNotIn(CLAVE_CANASTA, self.client.session)

    def test_ver_checkout_no_descuenta_stock(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 1}
        )
        respuesta = self.client.get(reverse("pedidos:checkout"))
        self.assertEqual(respuesta.status_code, 200)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 5)

    def test_comprobante_inexistente_redirige(self):
        respuesta = self.client.get(reverse("pedidos:comprobante"))
        self.assertRedirects(respuesta, reverse("pedidos:ver_canasta"))

    def test_cerrar_comprobante(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 1}
        )
        self.client.post(reverse("pedidos:checkout"), self._datos_checkout())
        self.assertIn(CLAVE_COMPROBANTE, self.client.session)

        respuesta = self.client.post(reverse("pedidos:cerrar_comprobante"))
        self.assertRedirects(respuesta, reverse("core:inicio"))
        self.assertNotIn(CLAVE_COMPROBANTE, self.client.session)

    def test_folio_tiene_formato_institucional(self):
        self.client.post(
            reverse("pedidos:agregar", args=[self.producto.pk]), {"cantidad": 1}
        )
        self.client.post(reverse("pedidos:checkout"), self._datos_checkout())
        folio = self.client.session[CLAVE_COMPROBANTE]["folio"]
        self.assertTrue(re.fullmatch(r"VET-\d{4}-[A-Z0-9]{4}", folio))
