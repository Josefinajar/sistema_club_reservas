"""
CAPA 3 · ACCESO A DATOS
Todo el SQL de reservas vive acá. Nada de reglas de negocio: solo leer y escribir.

Los datos del usuario SIEMPRE van como parámetros (%s), nunca pegados al texto
del SQL. Eso evita inyección SQL y lo pide el enunciado.

>>> PUNTO A CONFIRMAR CON EL GRUPO <<<
Usa las tablas del init_db.sql del grupo: canchas(id, activa, precio_hora),
socios(id, activo) y reservas (con la tarifa guardada en `tarifa_historica`).
"""
from datetime import timedelta

COLUMNAS = """id, id_socio, id_cancha, fecha_hora_inicio, fecha_hora_fin,
              estado, tarifa_historica, total"""


# ---------- socios y canchas (tablas del grupo) ----------

def buscar_socio(cursor, id_socio):
    # FOR UPDATE "traba" la fila hasta el commit: si llegan dos pedidos a la vez
    # para el mismo socio, el segundo espera a que el primero termine.
    cursor.execute("SELECT id, activo FROM socios WHERE id = %s FOR UPDATE", (id_socio,))
    return cursor.fetchone()


def buscar_cancha(cursor, id_cancha):
    cursor.execute(
        "SELECT id, activa, precio_hora FROM canchas WHERE id = %s FOR UPDATE", (id_cancha,)
    )
    return cursor.fetchone()


# ---------- superposiciones ----------
# Dos intervalos se pisan si  inicio_existente < fin_nuevo  Y  inicio_nuevo < fin_existente.
# Con esa sola condición quedan cubiertos los casos parciales, iguales, contenidos
# y contenedores. Las consecutivas (18-20 y 20-21) NO se pisan.

def hay_superposicion_cancha(cursor, id_cancha, inicio, fin):
    cursor.execute(
        """SELECT 1 FROM reservas
           WHERE id_cancha = %s AND estado = 'confirmada'
             AND fecha_hora_inicio < %s AND %s < fecha_hora_fin
           LIMIT 1""",
        (id_cancha, fin, inicio),
    )
    return cursor.fetchone() is not None


def hay_superposicion_socio(cursor, id_socio, inicio, fin):
    cursor.execute(
        """SELECT 1 FROM reservas
           WHERE id_socio = %s AND estado = 'confirmada'
             AND fecha_hora_inicio < %s AND %s < fecha_hora_fin
           LIMIT 1""",
        (id_socio, fin, inicio),
    )
    return cursor.fetchone() is not None


# ---------- reservas ----------

def insertar_reserva(cursor, id_socio, id_cancha, inicio, fin, tarifa_historica, total):
    cursor.execute(
        """INSERT INTO reservas
             (id_socio, id_cancha, fecha_hora_inicio, fecha_hora_fin, estado, tarifa_historica, total)
           VALUES (%s, %s, %s, %s, 'confirmada', %s, %s)""",
        (id_socio, id_cancha, inicio, fin, tarifa_historica, total),
    )
    return cursor.lastrowid


def obtener_reserva(cursor, id_reserva, bloquear=False):
    sql = f"SELECT {COLUMNAS} FROM reservas WHERE id = %s"
    if bloquear:
        sql += " FOR UPDATE"
    cursor.execute(sql, (id_reserva,))
    return cursor.fetchone()


def actualizar_estado(cursor, id_reserva, estado):
    cursor.execute("UPDATE reservas SET estado = %s WHERE id = %s", (estado, id_reserva))


def listar_reservas(cursor, filtros, limit, offset):
    """Devuelve (filas de la página pedida, total de filas que cumplen los filtros)."""
    condiciones, valores = [], []
    for campo in ("id_cancha", "id_socio", "estado"):
        if campo in filtros:
            condiciones.append(f"{campo} = %s")  # el nombre de columna es fijo, no viene del usuario
            valores.append(filtros[campo])
    # El rango de fechas se aplica al día en que se usa la cancha (ambos extremos incluidos)
    if "fecha_desde" in filtros:
        condiciones.append("fecha_hora_inicio >= %s")
        valores.append(filtros["fecha_desde"])
    if "fecha_hasta" in filtros:
        condiciones.append("fecha_hora_inicio < %s")
        valores.append(filtros["fecha_hasta"] + timedelta(days=1))

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    cursor.execute(f"SELECT COUNT(*) AS total FROM reservas {where}", valores)
    total = cursor.fetchone()["total"]

    cursor.execute(
        f"SELECT {COLUMNAS} FROM reservas {where} ORDER BY id ASC LIMIT %s OFFSET %s",
        valores + [limit, offset],
    )
    return cursor.fetchall(), total
