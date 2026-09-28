from app.constants import (
    ERROR_CODE_CANCHA_NOT_FOUND,
    ERROR_CODE_RESERVA_NOT_FOUND,
    ERROR_CODE_SOCIO_NOT_FOUND,
)
from app.db import obtener_conexion
from app.queries import reservas_queries
from app.validators.reservas_validator import ErrorReserva, ahora, validar_intervalo

FORMATO_FECHA_HORA = '%Y-%m-%dT%H:%M:%S.%f-03:00'

ERROR_CODE_SOCIO_INACTIVO = 'socio.inactive'
ERROR_CODE_CANCHA_INACTIVA = 'cancha.inactive'
ERROR_CODE_SUPERPOSICION_CANCHA = 'reserva.overlap.cancha'
ERROR_CODE_SUPERPOSICION_SOCIO = 'reserva.overlap.socio'
ERROR_CODE_TRANSICION_INVALIDA = 'reserva.invalid.transition'


def _formatear(reserva: dict) -> dict:
    return {
        **reserva,
        'fecha_hora_inicio': reserva['fecha_hora_inicio'].strftime(FORMATO_FECHA_HORA),
        'fecha_hora_fin': reserva['fecha_hora_fin'].strftime(FORMATO_FECHA_HORA),
    }


def _no_encontrado(code: str, recurso: str, id_recurso: int) -> ErrorReserva:
    return ErrorReserva(404, code, 'Recurso no encontrado', f'No existe {recurso} con id {id_recurso}')


def _conflicto(code: str, description: str) -> ErrorReserva:
    return ErrorReserva(409, code, 'Conflicto de negocio', description)


def crear_reserva(datos: dict) -> dict:
    """
    Crea una reserva confirmada. Todas las verificaciones y el INSERT ocurren
    en una misma transacción: si alguna falla, no se guarda nada.
    """
    horas = validar_intervalo(datos['inicio'], datos['fin'])

    with obtener_conexion() as conexion:
        with conexion.begin():
            socio = reservas_queries.bloquear_socio(conexion, datos['id_socio'])
            if socio is None:
                raise _no_encontrado(ERROR_CODE_SOCIO_NOT_FOUND, 'un socio', datos['id_socio'])
            if not socio['activo']:
                raise _conflicto(ERROR_CODE_SOCIO_INACTIVO, 'El socio está inactivo')

            cancha = reservas_queries.bloquear_cancha(conexion, datos['id_cancha'])
            if cancha is None:
                raise _no_encontrado(ERROR_CODE_CANCHA_NOT_FOUND, 'una cancha', datos['id_cancha'])
            if not cancha['activa']:
                raise _conflicto(ERROR_CODE_CANCHA_INACTIVA, 'La cancha está inactiva')

            if reservas_queries.existe_superposicion(conexion, 'id_cancha', cancha['id'], datos['inicio'], datos['fin']):
                raise _conflicto(ERROR_CODE_SUPERPOSICION_CANCHA,
                                 'La cancha ya tiene una reserva confirmada en ese horario')
            if reservas_queries.existe_superposicion(conexion, 'id_socio', socio['id'], datos['inicio'], datos['fin']):
                raise _conflicto(ERROR_CODE_SUPERPOSICION_SOCIO,
                                 'El socio ya tiene una reserva confirmada en ese horario')

            # Se guarda la tarifa vigente para que cambios de precio posteriores no alteren la reserva
            precio_hora = cancha['precio_hora']
            id_reserva = reservas_queries.insertar_reserva(
                conexion, socio['id'], cancha['id'], datos['inicio'], datos['fin'],
                precio_hora, horas * precio_hora,
            )
            reserva = reservas_queries.obtener_reserva(conexion, id_reserva)

    return _formatear(reserva)


def listar_reservas(filtros: dict, limit: int, offset: int) -> tuple[list[dict], int]:
    reservas, total = reservas_queries.listar_reservas(filtros, limit, offset)
    return [_formatear(r) for r in reservas], total


def obtener_reserva(id_reserva: int) -> dict:
    reserva = reservas_queries.obtener_reserva_por_id(id_reserva)
    if reserva is None:
        raise _no_encontrado(ERROR_CODE_RESERVA_NOT_FOUND, 'una reserva', id_reserva)
    return _formatear(reserva)


def cambiar_estado(id_reserva: int, nuevo_estado: str) -> dict:
    """
    Transiciones permitidas:
      confirmada -> cancelada   si todavía no comenzó
      confirmada -> finalizada  si ya terminó
    Repetir el estado actual no modifica la reserva.
    """
    with obtener_conexion() as conexion:
        with conexion.begin():
            reserva = reservas_queries.obtener_reserva(conexion, id_reserva, bloquear=True)
            if reserva is None:
                raise _no_encontrado(ERROR_CODE_RESERVA_NOT_FOUND, 'una reserva', id_reserva)

            actual = reserva['estado']
            if nuevo_estado != actual:
                if actual != 'confirmada':
                    raise _conflicto(ERROR_CODE_TRANSICION_INVALIDA,
                                     f'Una reserva {actual} no puede cambiar de estado')
                momento = ahora()
                if nuevo_estado == 'cancelada' and momento >= reserva['fecha_hora_inicio']:
                    raise _conflicto(ERROR_CODE_TRANSICION_INVALIDA,
                                     'Solo se puede cancelar una reserva que todavía no comenzó')
                if nuevo_estado == 'finalizada' and momento < reserva['fecha_hora_fin']:
                    raise _conflicto(ERROR_CODE_TRANSICION_INVALIDA,
                                     'Solo se puede finalizar una reserva que ya terminó')
                reservas_queries.actualizar_estado(conexion, id_reserva, nuevo_estado)
                reserva['estado'] = nuevo_estado

    return _formatear(reserva)
