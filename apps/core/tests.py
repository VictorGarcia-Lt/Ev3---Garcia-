"""Pruebas de las páginas institucionales."""
from django.test import TestCase
from django.urls import reverse

from apps.catalogo.models import CategoriaProducto, Producto


class PaginasPublicasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = CategoriaProducto.objects.create(
            nombre="Alimentos y Nutrición",
            descripcion="Alimentos para mascotas.",
        )
        Producto.objects.create(
            categoria=cls.categoria,
            codigo="ALI-001",
            nombre="Alimento premium",
            descripcion="Alimento balanceado para perros adultos.",
            marca="NutriCan",
            precio="19990",
            stock=10,
        )

    def test_inicio_responde_y_muestra_destacados(self):
        respuesta = self.client.get(reverse("core:inicio"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "VetCare Central")
        self.assertContains(respuesta, "Alimento premium")
        self.assertContains(respuesta, "Productos destacados")

    def test_pagina_nosotros(self):
        respuesta = self.client.get(reverse("core:nosotros"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Quiénes somos")
        self.assertContains(respuesta, "tienda de productos para mascotas")

    def test_pagina_contacto(self):
        respuesta = self.client.get(reverse("core:contacto"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Horario de tienda")
