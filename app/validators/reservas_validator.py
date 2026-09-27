import re
from datetime import date, datetime, timedelta, timezone

from app.constants import ERROR_CODE_INVALID_BODY, MIN_ID
from app.utils import construir_error_api

ZONA_HORARIA = timezone(timedelta(hours=-3))
PATRON_FECHA_HORA = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}-03:00$')
PATRON_FECHA = re.compile(r'^\d{4}-\d{2}-\d{2}$')
PATRON_ENTERO = re.compile(r'^\d+$')

HORA_APERTURA = 8
HORA_CIERRE = 23
DURACION_MINIMA_HORAS = 1
DURACION_MAXIMA_HORAS = 3
ESTADOS_RESERVA = ('confirmada', 'cancelada', 'finalizada')

LIMIT_POR_DEFECTO = 10
LIMIT_MAXIMO = 100

CAMPOS_RESERVA = {'id_socio', 'id_cancha', 'fecha_hora_inicio', 'fecha_hora_fin'}
FILTROS_LISTADO = {'id_cancha', 'id_socio', 'estado', 'fecha_desde', 'fecha_hasta', '_limit', '_offset'}

ERROR_CODE_INVALID_QUERY = 'invalid.query.param'
ERROR_CODE_INVALID_INTERVAL = 'reserva.invalid.interval'


class ErrorReserva(Exception):
    """Error de negocio o de validación con su código HTTP y el payload de la API."""

    def __init__(self, status: int, code: str, message: str, description: str):
        super().__init__(description)
        self.status = status
        self.payload = construir_error_api(code=code, message=message, description=description)


def error_validacion(description: str, code: str = ERROR_CODE_INVALID_BODY) -> ErrorReserva:
    return ErrorReserva(400, code, 'Solicitud inválida', description)


def ahora() -> datetime:
    """Fecha y hora actual en GMT-3, sin zona horaria (igual que en la base)."""
    return datetime.now(ZONA_HORARIA).replace(tzinfo=None)


# ---------------------------------------------------------------
# Valores individuales
# ---------------------------------------------------------------

def validar_id(valor, campo: str) -> int:
    # bool es subclase de int en Python: se excluye para no aceptar true/false como ids
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < MIN_ID:
        raise error_validacion(f"El campo '{campo}' debe ser un entero positivo")
    return valor


def parsear_fecha_hora(valor, campo: str) -> datetime:
    if not isinstance(valor, str) or not PATRON_FECHA_HORA.match(valor):
        raise error_validacion(f"El campo '{campo}' debe tener formato YYYY-MM-DDTHH:MM:SS.ffffff-03:00")
    try:
        return datetime.fromisoformat(valor).replace(tzinfo=None)
    except ValueError:
        raise error_validacion(f"El campo '{campo}' no es una fecha y hora válida")


def validar_intervalo(inicio: datetime, fin: datetime) -> int:
    """Aplica las reglas de horario del club y devuelve la duración en horas."""
    for momento, campo in ((inicio, 'fecha_hora_inicio'), (fin, 'fecha_hora_fin')):
        if momento.minute or momento.second or momento.microsecond:
            raise error_validacion(f"El campo '{campo}' debe ser una hora en punto", ERROR_CODE_INVALID_INTERVAL)
    if inicio >= fin:
        raise error_validacion('fecha_hora_inicio debe ser anterior a fecha_hora_fin', ERROR_CODE_INVALID_INTERVAL)
    if inicio.date() != fin.date():
        raise error_validacion('La reserva no puede atravesar la medianoche', ERROR_CODE_INVALID_INTERVAL)
    if inicio.hour < HORA_APERTURA or fin.hour > HORA_CIERRE:
        raise error_validacion('La reserva debe estar dentro del horario del club (08:00 a 23:00)',
                               ERROR_CODE_INVALID_INTERVAL)
    horas = (fin - inicio) // timedelta(hours=1)
    if not DURACION_MINIMA_HORAS <= horas <= DURACION_MAXIMA_HORAS:
        raise error_validacion('La reserva debe durar entre 1 y 3 horas', ERROR_CODE_INVALID_INTERVAL)
    if inicio <= ahora():
        raise error_validacion('La reserva debe comenzar en el futuro', ERROR_CODE_INVALID_INTERVAL)
    return horas


# ---------------------------------------------------------------
# Cuerpos JSON
# ---------------------------------------------------------------

def _validar_objeto(cuerpo) -> None:
    if not isinstance(cuerpo, dict) or not cuerpo:
        raise error_validacion('El cuerpo debe ser un objeto JSON no vacío')


def validar_reserva_nueva(cuerpo) -> dict:
    _validar_objeto(cuerpo)
    desconocidos = set(cuerpo) - CAMPOS_RESERVA
    if desconocidos:
        raise error_validacion(f"Campos no permitidos: {', '.join(sorted(desconocidos))}")
    faltantes = CAMPOS_RESERVA - set(cuerpo)
    if faltantes:
        raise error_validacion(f"Faltan campos obligatorios: {', '.join(sorted(faltantes))}")
    return {
        'id_socio': validar_id(cuerpo['id_socio'], 'id_socio'),
        'id_cancha': validar_id(cuerpo['id_cancha'], 'id_cancha'),
        'inicio': parsear_fecha_hora(cuerpo['fecha_hora_inicio'], 'fecha_hora_inicio'),
        'fin': parsear_fecha_hora(cuerpo['fecha_hora_fin'], 'fecha_hora_fin'),
    }


def validar_estado(cuerpo) -> str:
    _validar_objeto(cuerpo)
    desconocidos = set(cuerpo) - {'estado'}
    if desconocidos:
        raise error_validacion(f"Campos no permitidos: {', '.join(sorted(desconocidos))}")
    estado = cuerpo.get('estado')
    if estado not in ESTADOS_RESERVA:
        raise error_validacion(f"El campo 'estado' debe ser uno de: {', '.join(ESTADOS_RESERVA)}")
    return estado


# ---------------------------------------------------------------
# Parámetros de consulta del listado
# ---------------------------------------------------------------

def _entero_query(texto: str, campo: str, minimo: int) -> int:
    if not PATRON_ENTERO.match(texto) or int(texto) < minimo:
        raise error_validacion(f"El parámetro '{campo}' debe ser un entero mayor o igual a {minimo}",
                               ERROR_CODE_INVALID_QUERY)
    return int(texto)


def _fecha_query(texto: str, campo: str) -> date:
    if not PATRON_FECHA.match(texto):
        raise error_validacion(f"El parámetro '{campo}' debe tener formato YYYY-MM-DD", ERROR_CODE_INVALID_QUERY)
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise error_validacion(f"El parámetro '{campo}' no es una fecha válida", ERROR_CODE_INVALID_QUERY)


def validar_filtros(args) -> dict:
    desconocidos = set(args.keys()) - FILTROS_LISTADO
    if desconocidos:
        raise error_validacion(f"Parámetros no permitidos: {', '.join(sorted(desconocidos))}",
                               ERROR_CODE_INVALID_QUERY)
    filtros = {}
    for campo in ('id_cancha', 'id_socio'):
        if campo in args:
            filtros[campo] = _entero_query(args[campo], campo, MIN_ID)
    if 'estado' in args:
        if args['estado'] not in ESTADOS_RESERVA:
            raise error_validacion(f"El parámetro 'estado' debe ser uno de: {', '.join(ESTADOS_RESERVA)}",
                                   ERROR_CODE_INVALID_QUERY)
        filtros['estado'] = args['estado']
    for campo in ('fecha_desde', 'fecha_hasta'):
        if campo in args:
            filtros[campo] = _fecha_query(args[campo], campo)
    if 'fecha_desde' in filtros and 'fecha_hasta' in filtros and filtros['fecha_desde'] > filtros['fecha_hasta']:
        raise error_validacion('fecha_desde debe ser menor o igual a fecha_hasta', ERROR_CODE_INVALID_QUERY)
    return filtros


def validar_paginacion(args) -> tuple[int, int]:
    limit = _entero_query(args['_limit'], '_limit', 1) if '_limit' in args else LIMIT_POR_DEFECTO
    offset = _entero_query(args['_offset'], '_offset', 0) if '_offset' in args else 0
    if limit > LIMIT_MAXIMO:
        raise error_validacion(f"El parámetro '_limit' debe estar entre 1 y {LIMIT_MAXIMO}", ERROR_CODE_INVALID_QUERY)
    return limit, offset
