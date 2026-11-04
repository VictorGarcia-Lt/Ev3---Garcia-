"""Lógica de la canasta de compras almacenada en request.session."""
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError

from apps.catalogo.models import Producto

CLAVE_CANASTA = "canasta_vetcare"
CLAVE_COMPROBANTE = "comprobante_vetcare"
IVA = Decimal("0.19")
MAX_UNIDADES_POR_ITEM = 20


def _leer_canasta(session):
    """Devuelve la canasta normalizada como {id: {'cantidad': n}}."""
    datos = session.get(CLAVE_CANASTA, {})
    if not isinstance(datos, dict):
        return {}

    canasta = {}
    for clave, valor in datos.items():
        try:
            if isinstance(valor, dict):
                cantidad = int(valor.get("cantidad", 0))
            else:
                cantidad = int(valor)
        except (TypeError, ValueError):
            continue
        if cantidad > 0:
            canasta[str(clave)] = {"cantidad": min(cantidad, MAX_UNIDADES_POR_ITEM)}
    return canasta


def _guardar_canasta(session, canasta):
    if canasta:
        session[CLAVE_CANASTA] = canasta
    else:
        session.pop(CLAVE_CANASTA, None)
    session.modified = True


def _validar_cantidad(cantidad):
    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        raise ValidationError("La cantidad debe ser un número entero.") from None
    if cantidad < 1:
        raise ValidationError("La cantidad mínima es 1 unidad.")
    if cantidad > MAX_UNIDADES_POR_ITEM:
        raise ValidationError(
            f"Puedes solicitar hasta {MAX_UNIDADES_POR_ITEM} unidades por ítem."
        )
    return cantidad


def _validar_disponibilidad(producto, cantidad):
    if not producto.activo or not producto.categoria.activo:
        raise ValidationError(
            f"«{producto.nombre}» no se encuentra vigente en el catálogo."
        )
    if producto.estado != Producto.Estado.DISPONIBLE:
        raise ValidationError(
            f"«{producto.nombre}» no está disponible: {producto.get_estado_display()}."
        )
    stock = producto.stock or 0
    if stock <= 0:
        raise ValidationError(f"«{producto.nombre}» está agotado.")
    if cantidad > stock:
        raise ValidationError(
            f"Solo hay {stock} unidad(es) de «{producto.nombre}» en stock."
        )


def agregar_item(session, producto, cantidad=1):
    """Agrega unidades validando disponibilidad y stock."""
    cantidad = _validar_cantidad(cantidad)
    canasta = _leer_canasta(session)
    clave = str(producto.pk)
    actual = canasta.get(clave, {}).get("cantidad", 0)
    nueva_cantidad = actual + cantidad

    if nueva_cantidad > MAX_UNIDADES_POR_ITEM:
        raise ValidationError(
            f"La canasta admite hasta {MAX_UNIDADES_POR_ITEM} unidades por ítem."
        )
    _validar_disponibilidad(producto, nueva_cantidad)

    canasta[clave] = {"cantidad": nueva_cantidad}
    _guardar_canasta(session, canasta)
    return nueva_cantidad


def actualizar_item(session, producto, cantidad):
    """Fija la cantidad exacta de un ítem de la canasta."""
    cantidad = _validar_cantidad(cantidad)
    canasta = _leer_canasta(session)
    clave = str(producto.pk)

    if clave not in canasta:
        raise ValidationError("El ítem ya no se encuentra en la canasta.")

    _validar_disponibilidad(producto, cantidad)
    canasta[clave] = {"cantidad": cantidad}
    _guardar_canasta(session, canasta)
    return cantidad


def quitar_item(session, producto_id):
    """Elimina un ítem individual de la canasta."""
    canasta = _leer_canasta(session)
    canasta.pop(str(producto_id), None)
    _guardar_canasta(session, canasta)


def vaciar_canasta(session):
    """Elimina la canasta completa de la sesión."""
    session.pop(CLAVE_CANASTA, None)
    session.modified = True


def obtener_items(session):
    """Devuelve los ítems vigentes y descarta los que dejaron de estar disponibles."""
    canasta = _leer_canasta(session)
    if not canasta:
        return [], []

    productos = {
        str(producto.pk): producto
        for producto in Producto.objects.select_related("categoria").filter(
            pk__in=canasta.keys()
        )
    }

    items = []
    invalidos = []
    canasta_normalizada = {}

    for clave, entrada in canasta.items():
        producto = productos.get(clave)
        if producto is None:
            continue

        cantidad = entrada["cantidad"]

        if not producto.disponible:
            invalidos.append(producto)
            continue

        stock = producto.stock or 0
        if cantidad > stock:
            cantidad = stock
        if cantidad == 0:
            invalidos.append(producto)
            continue

        canasta_normalizada[clave] = {"cantidad": cantidad}
        items.append(
            {
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": producto.precio * cantidad,
            }
        )

    if canasta_normalizada != canasta:
        _guardar_canasta(session, canasta_normalizada)

    items.sort(key=lambda item: item["producto"].nombre.lower())
    return items, invalidos


def obtener_items_para_compra(session, bloquear=False):
    """Valida la canasta de forma estricta antes de descontar stock.

    A diferencia de ``obtener_items``, no recorta cantidades: si un producto
    cambió de stock, la compra se rechaza para que el usuario revise la canasta.
    ``bloquear=True`` debe usarse dentro de ``transaction.atomic()``.
    """
    canasta = _leer_canasta(session)
    if not canasta:
        return [], []

    consulta = Producto.objects.select_related("categoria").filter(
        pk__in=canasta.keys()
    )
    if bloquear:
        consulta = consulta.select_for_update()

    productos = {str(producto.pk): producto for producto in consulta}
    items = []
    invalidos = []

    for clave, entrada in canasta.items():
        producto = productos.get(clave)
        if producto is None:
            continue

        cantidad = entrada["cantidad"]
        try:
            _validar_disponibilidad(producto, cantidad)
        except ValidationError:
            invalidos.append(producto)
            continue

        items.append(
            {
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": producto.precio * cantidad,
            }
        )

    items.sort(key=lambda item: item["producto"].nombre.lower())
    return items, invalidos


def descontar_stock(items):
    """Descuenta las unidades compradas y marca como agotado si corresponde.

    Debe invocarse dentro de una transacción para que la compra sea atómica.
    """
    for item in items:
        producto = item["producto"]
        cantidad = item["cantidad"]

        stock_actual = producto.stock or 0
        if cantidad > stock_actual:
            raise ValidationError(f"Stock insuficiente para «{producto.nombre}».")

        producto.stock = stock_actual - cantidad
        if producto.stock == 0:
            producto.estado = Producto.Estado.AGOTADO
        producto.save(update_fields=["stock", "estado", "actualizado_en"])


def calcular_totales(items):
    """Calcula subtotal, IVA 19% y total final estimado en CLP."""
    subtotal = sum((item["subtotal"] for item in items), Decimal("0"))
    iva = (subtotal * IVA).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    total = subtotal + iva
    return {
        "subtotal": subtotal,
        "iva": iva,
        "total": total,
        "tasa_iva": int(IVA * 100),
        "total_items": sum(item["cantidad"] for item in items),
    }


def contar_unidades(session):
    """Cuenta las unidades almacenadas (usado por el context processor)."""
    return sum(entrada["cantidad"] for entrada in _leer_canasta(session).values())
