# VetCare Central & Pet Shop

Tienda en línea de productos para mascotas desarrollada con Django 5 para la Evaluación Sumativa 3 de Programación Back End.

## Ficha de la propuesta

- **Nombre del proyecto:** VetCare Central & Pet Shop.
- **Tipo de solución:** comercio electrónico de productos para mascotas.
- **Evaluación:** Evaluación Sumativa 3 — Programación Back End (INACAP).
- **Integrante:** Victor García.
- **Tecnologías:** Django 5.2, SQLite, Bootstrap 5, Pillow y python-dotenv.
- **Alcance:** venta de alimentos, higiene, accesorios y productos de cuidado para mascotas. No incluye servicios clínicos, agenda de horas ni peluquería.
- **Funcionalidades principales:** catálogo con búsqueda y filtros, CRUD protegido para personal autorizado, canasta en sesión, checkout simulado, comprobante de compra, autenticación y perfil de usuario.

## Guía de instalación

1. Clonar el repositorio e ingresar a la carpeta del proyecto:

   ```bash
   git clone https://github.com/VictorGarcia-Lt/Ev3---Garcia-.git
   cd "Ev3---Garcia-"
   ```

2. Crear y activar el entorno virtual:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   En Windows:

   ```bash
   .venv\Scripts\activate
   ```

3. Instalar las dependencias fijadas:

   ```bash
   pip install -r requirements.txt
   ```

4. Crear el archivo de variables de entorno a partir del ejemplo:

   ```bash
   cp .env.example .env
   ```

   Editar `.env` y reemplazar `DJANGO_SECRET_KEY` por una clave segura.

5. Aplicar las migraciones y cargar los datos de demostración:

   ```bash
   python manage.py migrate
   python manage.py poblar_datos
   ```

6. Ejecutar el servidor:

   ```bash
   python manage.py runserver
   ```

7. Abrir `http://127.0.0.1:8000/` en el navegador.

Para verificar el proyecto:

```bash
python manage.py check
python manage.py test
```

La suite actual contiene 63 pruebas automatizadas.

## Credenciales de prueba

| Perfil | Usuario | Contraseña | Acceso principal |
|---|---|---|---|
| Administrador | `admin` | `admin123` | `/admin/` y gestión del catálogo |
| Cliente | `cliente` | `cliente123` | Compra en el catálogo y perfil |

Las credenciales se crean al ejecutar `python manage.py poblar_datos`.

## Rutas principales

| Ruta | Descripción |
|---|---|
| `/` | Página de inicio. |
| `/catalogo/` | Catálogo público con búsqueda, filtros, orden y paginación. |
| `/catalogo/<slug>/` | Ficha de detalle de un producto. |
| `/canasta/` | Canasta de compras almacenada en la sesión. |
| `/canasta/checkout/` | Formulario de checkout y confirmación de compra. |
| `/canasta/comprobante/` | Comprobante simulado de la compra. |
| `/usuarios/login/` | Inicio de sesión. |
| `/usuarios/registro/` | Registro público de clientes. |
| `/usuarios/perfil/` | Perfil del usuario autenticado. |
| `/admin/` | Panel de administración de Django. |

## Bitácora de uso de Inteligencia Artificial


### 1. Arquitectura del proyecto

Prompt:

Diseña la arquitectura de un proyecto Django 5 para una clínica veterinaria y pet shop. Separa el código en las apps "core", "usuarios", "catalogo" y "pedidos", e indica qué modelos, vistas, formularios y plantillas debe tener cada una.

Respuesta de la IA: propuso la estructura de apps, la separación de responsabilidades y el orden de implementación de modelos, admin, CRUD y plantillas.

daptación crítica: se aceptó la separación modular porque facilita el mantenimiento y cumple con la pauta. Se ajustaron los "AppConfig" para que las apps se importen como "apps.core", "apps.usuarios", "apps.catalogo" y "apps.pedidos", y se completaron los archivos estándar que faltaban en "core" y "pedidos".

---

### 2. Modelo de datos y ORM

Prompt:

Genera los modelos "EspecialidadServicio" y "PrestacionProducto" para una clínica veterinaria. Usa "ForeignKey" con "PROTECT", "MinValueValidator", "choices" para los estados, "ImageField" y slug automático. Agrega validaciones para que los servicios usen duración y los productos usen stock.

Respuesta de la IA: creó los modelos con los campos, relaciones, validadores, estados cerrados, imagen y baja lógica mediante el campo "activo".

Adaptación crítica: se mantuvieron las validaciones de la pauta y se agregó el método "clean()" para impedir combinaciones incoherentes, como un servicio con stock o un producto sin stock marcado como disponible. También se definió que un producto con stock cero debe quedar en estado "AGOTADO".

---

### 3. Seguridad y sesiones

Prompt:

 Implementa la seguridad de un proyecto Django con login, registro y perfil. Protege el CRUD con "@login_required" y "@user_passes_test", agrega "{% csrf_token %}" en los formularios POST y valida las redirecciones de retorno. Además, crea una canasta en "request.session" con checkout simulado.

Respuesta de la IA: generó el sistema de autenticación, los decoradores de acceso, el formulario CSRF, la canasta en sesión y el checkout con folio único.

Adaptación crítica: se aceptó el uso de "request.session" porque la canasta es temporal y no requiere persistencia. Se reforzó la seguridad con cookies "HttpOnly" y "SameSite=Lax", validación de redirecciones con "url_has_allowed_host_and_scheme" y revalidación del stock dentro de una transacción atómica.



### 4. Diseño web responsive

Prompt:

 Propón una interfaz con Bootstrap 5 para el catálogo, el detalle del producto, la canasta y el checkout. Usa navbar, tarjetas, badges de estado, formularios accesibles y un diseño responsive para móvil.

Respuesta de la IA: entregó una estructura visual con navbar, tarjetas, grillas, badges, mensajes flash y formularios con clases de Bootstrap.

Adaptación crítica: se mantuvo la base visual, pero se ajustaron los textos y componentes al dominio veterinario. Se reemplazaron elementos genéricos por tarjetas de productos, estados de stock, botones de compra y avisos para los servicios que se agendan en la clínica.


### 5. Pruebas y documentación

Prompt:

Escribe pruebas para el catálogo, el CRUD, el login, la canasta y el checkout. Verifica el cálculo del IVA, la generación del folio y el descuento de stock, y documenta la instalación y las rutas principales.

Respuesta de la IA: propuso casos de prueba para las vistas públicas, el CRUD protegido, la autenticación, la canasta y el checkout.

Adaptación crítica: se ejecutaron las pruebas y se corrigieron los casos que dependían de la versión anterior de la canasta. El resultado final fue de 61 pruebas aprobadas con "python manage.py test", además de "python manage.py check" sin errores.

---

## Uso ético de la IA

- La IA se utilizó como apoyo para generar borradores de código, estructura y documentación.
- Las respuestas fueron revisadas, ejecutadas y adaptadas al contexto real del proyecto.
- No se compartieron datos personales, credenciales reales ni información sensible.
- Las decisiones de arquitectura, seguridad y negocio se validaron con la pauta y las pruebas automatizadas.
- El código final fue comprendido y ajustado por el estudiante; la IA no reemplazó la revisión crítica ni la responsabilidad académica.
