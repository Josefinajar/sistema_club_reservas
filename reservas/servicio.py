"""
CAPA 2 · REGLAS DE NEGOCIO
Acá se decide si una reserva se puede crear o si un cambio de estado está permitido.
Usa validaciones.py para revisar los datos y repositorio.py para hablar con la base.

Todo se hace dentro de una transacción: si algo falla en el medio, rollback()
deshace todo y no queda ninguna reserva a medias.
"""
from db import obtener_conexion
from errores import ErrorApi

from . import repositorio
from .validaciones import ahora, validar_intervalo

FORMATO_SALIDA = "%Y-%m-%dT%H:%M:%S.%f-03:00"


def a_json(fila):
    """Convierte una fila de la base al formato que devuelve la API."""
    return {
        "id": fila["id"],
        "id_socio": fila["id_socio"],
        "id_cancha": fila["id_cancha"],
        "fecha_hora_inicio": fila["fecha_hora_inicio"].strftime(FORMATO_SALIDA),
        "fecha_hora_fin": fila["fecha_hora_fin"].strftime(FORMATO_SALIDA),
        "estado": fila["estado"],
        "tarifa_historica": fila["tarifa_historica"],
        "total": fila["total"],
    }


def _en_transaccion(funcion):
    """Ejecuta `funcion(cursor)`; si sale bien hace commit, si falla hace rollback."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            resultado = funcion(cursor)
        conexion.commit()
        return resultado
    except Exception:
        conexion.rollback()
        raise


# ---------- POST /reservas ----------

def crear_reserva(datos):
    horas = validar_intervalo(datos["inicio"], datos["fin"])

    def _crear(cursor):
        socio = repositorio.buscar_socio(cursor, datos["id_socio"])
        if socio is None:
            raise ErrorApi("El socio no existe", 404)
        if not socio["activo"]:
            raise ErrorApi("El socio está inactivo", 409)

        cancha = repositorio.buscar_cancha(cursor, datos["id_cancha"])
        if cancha is None:
            raise ErrorApi("La cancha no existe", 404)
        if not cancha["activa"]:
            raise ErrorApi("La cancha está inactiva", 409)

        if repositorio.hay_superposicion_cancha(cursor, cancha["id"], datos["inicio"], datos["fin"]):
            raise ErrorApi("La cancha ya tiene una reserva confirmada en ese horario", 409)
        if repositorio.hay_superposicion_socio(cursor, socio["id"], datos["inicio"], datos["fin"]):
            raise ErrorApi("El socio ya tiene una reserva confirmada en ese horario", 409)

        tarifa = cancha["precio_hora"]  # tarifa vigente: queda guardada en la reserva
        id_nueva = repositorio.insertar_reserva(
            cursor, socio["id"], cancha["id"], datos["inicio"], datos["fin"],
            tarifa, horas * tarifa,
        )
        return repositorio.obtener_reserva(cursor, id_nueva)

    return a_json(_en_transaccion(_crear))


# ---------- GET /reservas y GET /reservas/{id} ----------

def listar_reservas(filtros, limit, offset):
    filas, total = _en_transaccion(
        lambda cursor: repositorio.listar_reservas(cursor, filtros, limit, offset)
    )
    return [a_json(f) for f in filas], total


def obtener_reserva(id_reserva):
    fila = _en_transaccion(lambda cursor: repositorio.obtener_reserva(cursor, id_reserva))
    if fila is None:
        raise ErrorApi("La reserva no existe", 404)
    return a_json(fila)


# ---------- PUT /reservas/{id}/estado ----------
#   confirmada -> cancelada   solo si todavía no empezó
#   confirmada -> finalizada  solo si ya terminó
#   cancelada / finalizada    no cambian más
#   pedir el mismo estado que ya tiene -> 200 sin tocar nada

def cambiar_estado(id_reserva, nuevo_estado):
    def _cambiar(cursor):
        reserva = repositorio.obtener_reserva(cursor, id_reserva, bloquear=True)
        if reserva is None:
            raise ErrorApi("La reserva no existe", 404)

        actual = reserva["estado"]
        if nuevo_estado == actual:
            return reserva
        if actual != "confirmada":
            raise ErrorApi(f"Una reserva {actual} no puede cambiar de estado", 409)

        momento = ahora()
        if nuevo_estado == "cancelada" and momento >= reserva["fecha_hora_inicio"]:
            raise ErrorApi("Solo se puede cancelar una reserva que todavía no empezó", 409)
        if nuevo_estado == "finalizada" and momento < reserva["fecha_hora_fin"]:
            raise ErrorApi("Solo se puede finalizar una reserva que ya terminó", 409)

        repositorio.actualizar_estado(cursor, id_reserva, nuevo_estado)
        reserva["estado"] = nuevo_estado
        return reserva

    return a_json(_en_transaccion(_cambiar))
