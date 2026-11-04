"""Comando de poblado inicial de VetCare Central.

Uso:
    python manage.py poblar_datos
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalogo.models import CategoriaProducto, Producto
from apps.usuarios.models import Usuario

CATEGORIAS = [
    {
        "nombre": "Alimentos y Nutrición",
        "slug": "alimentos-nutricion",
        "descripcion": "Alimentos balanceados, snacks y premios para mascotas.",
    },
    {
        "nombre": "Farmacia y Cuidado",
        "slug": "farmacia-cuidado",
        "descripcion": "Productos de cuidado, higiene y bienestar para mascotas.",
    },
    {
        "nombre": "Higiene y Estética",
        "slug": "higiene-estetica",
        "descripcion": "Shampoos, cepillos y productos de higiene para mascotas.",
    },
    {
        "nombre": "Accesorios y Juguetes",
        "slug": "accesorios-juguetes",
        "descripcion": "Juguetes, camas, correas y accesorios para mascotas.",
    },
]

PRODUCTOS = [
    {
        "codigo": "FAR-001",
        "nombre": "Alimento premium perro adulto 15 kg",
        "categoria": "alimentos-nutricion",
        "descripcion": (
            "Alimento balanceado con proteína de pollo y arroz, formulado para "
            "perros adultos de razas medianas y grandes."
        ),
        "marca": "NutriCan",
        "precio": Decimal("34990"),
        "stock": 25,
        "estado": "DISPONIBLE",
    },
    {
        "codigo": "FAR-002",
        "nombre": "Antiparasitario pipeta para gatos",
        "categoria": "farmacia-cuidado",
        "descripcion": (
            "Solución tópica de amplio espectro contra pulgas, garrapatas y "
            "parásitos internos. Caja con 3 pipetas."
        ),
        "marca": "VetGuard",
        "precio": Decimal("8990"),
        "stock": 40,
        "estado": "DISPONIBLE",
    },
    {
        "codigo": "FAR-003",
        "nombre": "Shampoo hipoalergénico para mascotas",
        "categoria": "higiene-estetica",
        "descripcion": (
            "Shampoo con avena coloidal y pH neutro, ideal para pieles sensibles. "
            "Frasco de 500 ml."
        ),
        "marca": "PetCare",
        "precio": Decimal("12990"),
        "stock": 18,
        "estado": "DISPONIBLE",
    },
    {
        "codigo": "FAR-004",
        "nombre": "Snacks dentales para perros",
        "categoria": "alimentos-nutricion",
        "descripcion": (
            "Snacks masticables que ayudan a reducir el sarro y refrescan el "
            "aliento. Bolsa de 200 g."
        ),
        "marca": "DentalPet",
        "precio": Decimal("5990"),
        "stock": 0,
        "estado": "AGOTADO",
    },
    {
        "codigo": "FAR-005",
        "nombre": "Suplemento articular senior",
        "categoria": "farmacia-cuidado",
        "descripcion": (
            "Condroprotector con glucosamina y condroitina para perros mayores "
            "con movilidad reducida. Frasco de 60 comprimidos."
        ),
        "marca": "VetFlex",
        "precio": Decimal("18990"),
        "stock": 12,
        "estado": "SUSPENDIDO",
    },
    {
        "codigo": "ALI-001",
        "nombre": "Alimento balanceado gato adulto 3 kg",
        "categoria": "alimentos-nutricion",
        "descripcion": (
            "Fórmula con proteína animal y taurina para gatos adultos. "
            "Bolsa resellable de 3 kg."
        ),
        "marca": "FelixCan",
        "precio": Decimal("19990"),
        "stock": 20,
        "estado": "DISPONIBLE",
    },
    {
        "codigo": "ALI-002",
        "nombre": "Alimento para cachorro 10 kg",
        "categoria": "alimentos-nutricion",
        "descripcion": (
            "Alimento con calcio y proteínas para el crecimiento de cachorros "
            "de razas medianas. Bolsa de 10 kg."
        ),
        "marca": "NutriCan",
        "precio": Decimal("27990"),
        "stock": 14,
        "estado": "DISPONIBLE",
    },
    {
        "codigo": "HIG-001",
        "nombre": "Cepillo deslanador",
        "categoria": "higiene-estetica",
        "descripcion": (
            "Cepillo con cerdas suaves y botón de limpieza para retirar el pelo "
            "suelto sin maltratar la piel."
        ),
        "marca": "PetCare",
        "precio": Decimal("7990"),
        "stock": 30,
        "estado": "DISPONIBLE",
    },
    {
        "codigo": "HIG-002",
        "nombre": "Toallitas higiénicas para mascotas",
        "categoria": "higiene-estetica",
        "descripcion": (
            "Paquete de 80 toallitas húmedas sin alcohol para limpieza diaria "
            "de patas y pelaje."
        ),
        "marca": "CleanPet",
        "precio": Decimal("4490"),
        "stock": 45,
        "estado": "DISPONIBLE",
    },
    {
        "codigo": "ACC-001",
        "nombre": "Juguete mordedor resistente",
        "categoria": "accesorios-juguetes",
        "descripcion": (
            "Juguete de caucho natural para perros medianos y grandes. "
            "Ayuda a mantener una masticación saludable."
        ),
        "marca": "PlayPet",
        "precio": Decimal("9990"),
        "stock": 22,
        "estado": "DISPONIBLE",
    },
    {
        "codigo": "ACC-002",
        "nombre": "Cama ortopédica mediana",
        "categoria": "accesorios-juguetes",
        "descripcion": (
            "Cama acolchada con espuma de alta densidad y funda lavable, "
            "ideal para perros y gatos de tamaño mediano."
        ),
        "marca": "DreamPaws",
        "precio": Decimal("29990"),
        "stock": 8,
        "estado": "DISPONIBLE",
    },
    {
        "codigo": "ACC-003",
        "nombre": "Correa reflectante ajustable",
        "categoria": "accesorios-juguetes",
        "descripcion": (
            "Correa de nylon reflectante con mosquetón metálico y largo "
            "ajustable para paseos seguros."
        ),
        "marca": "WalkPet",
        "precio": Decimal("8990"),
        "stock": 16,
        "estado": "DISPONIBLE",
    },
]


class Command(BaseCommand):
    help = (
        "Crea el administrador, el cliente de prueba, las categorías y los "
        "productos de demostración de VetCare Central."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Poblando VetCare Central..."))

        admin, creado = Usuario.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@vetcare.cl",
                "first_name": "Administrador",
                "last_name": "VetCare",
                "rol": Usuario.Rol.ADMINISTRATIVO,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if creado:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(
                self.style.SUCCESS("  ✓ Superusuario creado: admin / admin123")
            )
        else:
            cambios = False
            for campo, valor in (
                ("email", "admin@vetcare.cl"),
                ("is_staff", True),
                ("is_superuser", True),
            ):
                if getattr(admin, campo) != valor:
                    setattr(admin, campo, valor)
                    cambios = True
            if cambios:
                admin.save()
            self.stdout.write(
                self.style.WARNING(
                    "  · El usuario 'admin' ya existía; se conservó su contraseña."
                )
            )

        cliente, creado = Usuario.objects.get_or_create(
            username="cliente",
            defaults={
                "email": "cliente@vetcare.cl",
                "first_name": "Cliente",
                "last_name": "Demo",
                "rol": Usuario.Rol.CLIENTE,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        if creado:
            cliente.set_password("cliente123")
            cliente.save()
            self.stdout.write(
                self.style.SUCCESS("  ✓ Cliente creado: cliente / cliente123")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "  · El usuario 'cliente' ya existía; se conservó su contraseña."
                )
            )

        categorias = {}
        for datos in CATEGORIAS:
            categoria, creada = CategoriaProducto.objects.update_or_create(
                slug=datos["slug"],
                defaults={
                    "nombre": datos["nombre"],
                    "descripcion": datos["descripcion"],
                    "activo": True,
                },
            )
            categorias[datos["slug"]] = categoria
            estado = "creada" if creada else "actualizada"
            self.stdout.write(f"  ✓ Categoría {estado}: {categoria.nombre}")

        creados = 0
        actualizados = 0
        for datos in PRODUCTOS:
            categoria = categorias[datos["categoria"]]
            defaults = {
                "categoria": categoria,
                "nombre": datos["nombre"],
                "descripcion": datos["descripcion"],
                "marca": datos.get("marca", ""),
                "precio": datos["precio"],
                "stock": datos["stock"],
                "estado": datos["estado"],
                "activo": True,
            }
            producto, creado = Producto.objects.update_or_create(
                codigo=datos["codigo"],
                defaults=defaults,
            )
            if creado:
                creados += 1
            else:
                actualizados += 1
            self.stdout.write(f"    · {producto.codigo} — {producto.nombre}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Poblado finalizado: {len(categorias)} categorías, "
                f"{creados} productos nuevos y {actualizados} actualizados."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Acceso al panel: http://127.0.0.1:8000/admin/ "
                "(usuario: admin / contraseña: admin123)"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Acceso de cliente: http://127.0.0.1:8000/usuarios/login/ "
                "(usuario: cliente / contraseña: cliente123)"
            )
        )
