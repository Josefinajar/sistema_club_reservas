import logging
from re import sub
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from .constants import (
    DURACION_MAX_HORAS,
    DURACION_MIN_HORAS,
    ERROR_CODE_INVALID_BODY,
    ERROR_CODE_INVALID_MIN_VALUE,
    HORA_APERTURA,
    HORA_CIERRE,
    LIMIT_DEFAULT,
    LIMIT_MAX,
    LIMIT_MIN,
    OFFSET_DEFAULT,
)

logger = logging.getLogger(__name__)
GMT_MENOS_3 = timezone(timedelta(hours=-3))


def construir_error_api(code: str, message: str, description: str, level: str = 'error') -> dict:
    """Construye un payload de error compatible con el resto de la API."""
    return {
        'errors': [{
            'code': code,
            'message': message,
            'level': level,
            'description': description
        }]
    }


def validar_entero(numero, nombre: str = 'numero') -> int:
    valor = str(numero)
    valor_sin_letras = sub('[a-zA-Z]+', '', valor)

    try:
        return int(valor_sin_letras)
    except ValueError:
        logger.warning(f"Valor numerico invalido: '{numero}' no puede convertirse a entero")

        raise ValueError(construir_error_api(
            code=f'invalid.{nombre}.format',
            message=f"Formato de '{nombre}' invalido",
            description=f"El valor '{numero}' no puede convertirse a un numero entero"
        ))


def validar_minimo(valor: int, minimo: int, nombre: str) -> int:
    if valor < minimo:
        logger.warning(f"Valor por debajo del minimo: '{nombre}' es {valor}, minimo esperado {minimo}")

        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_MIN_VALUE,
            message='Valor por debajo del minimo permitido',
            description=f"El parametro '{nombre}' debe ser mayor o igual a {minimo}. Se recibio: {valor}"
        ))

    return valor


def validar_maximo(valor: int, maximo: int, nombre: str) -> int:
    if valor > maximo:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Valor por encima del maximo permitido',
            description=f"El parametro '{nombre}' debe ser menor o igual a {maximo}. Se recibio: {valor}"
        ))
    return valor


def validar_string_no_vacio(valor, nombre: str) -> str:
    if valor is None or not str(valor).strip():
        raise ValueError(construir_error_api(
            code=f'required.{nombre}',
            message=f"Campo requerido: '{nombre}'",
            description=f"El campo '{nombre}' es obligatorio y no puede estar vacio"
        ))

    return str(valor).strip()


def validar_bool(valor, nombre: str) -> bool:
    if not isinstance(valor, bool):
        raise ValueError(construir_error_api(
            code=f'invalid.{nombre}.format',
            message=f"Formato de '{nombre}' invalido",
            description=f"El campo '{nombre}' debe ser un booleano (true/false)"
        ))
    return valor


def validar_entero_query(valor, nombre: str) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ValueError(construir_error_api(
            code=f'invalid.{nombre}.format',
            message=f"Parametro '{nombre}' invalido",
            description=f"'{valor}' no es un numero entero valido"
        ))


def validar_bool_query(valor: str, nombre: str) -> bool:
    if valor == 'true':
        return True
    if valor == 'false':
        return False
    raise ValueError(construir_error_api(
        code=f'invalid.{nombre}.format',
        message=f"Parametro '{nombre}' invalido",
        description=f"'{nombre}' solo admite 'true' o 'false'"
    ))


def parse_pagination(args) -> tuple[int, int]:
    try:
        limit = int(args.get('_limit', LIMIT_DEFAULT))
        offset = int(args.get('_offset', OFFSET_DEFAULT))
    except (TypeError, ValueError):
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Parametros de paginacion invalidos',
            description="'_limit' y '_offset' deben ser numeros enteros"
        ))
    if not LIMIT_MIN <= limit <= LIMIT_MAX:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message="Parametro '_limit' invalido",
            description=f"'_limit' debe estar entre {LIMIT_MIN} y {LIMIT_MAX}"
        ))
    if offset < 0:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message="Parametro '_offset' invalido",
            description="'_offset' debe ser mayor o igual a cero"
        ))
    return limit, offset


def construir_links(request, total: int, limit: int, offset: int) -> dict:
    argumentos = request.args.to_dict(flat=True)

    def crear_link(nuevo_offset: int) -> dict:
        parametros = dict(argumentos)
        parametros['_limit'] = limit
        parametros['_offset'] = nuevo_offset
        return {'href': f'{request.base_url}?{urlencode(parametros)}'}

    ultimo_offset = ((total - 1) // limit) * limit if total else 0
    links = {'_first': crear_link(0), '_last': crear_link(ultimo_offset)}
    if offset > 0:
        links['_prev'] = crear_link(max(offset - limit, 0))
    if offset + limit < total:
        links['_next'] = crear_link(offset + limit)
    return links


def validar_intervalo_club(inicio: datetime, fin: datetime) -> None:
    if (inicio.minute, inicio.second, inicio.microsecond) != (0, 0, 0) or \
       (fin.minute, fin.second, fin.microsecond) != (0, 0, 0):
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Horario invalido',
            description='El intervalo debe comenzar y terminar en una hora en punto'
        ))
    if inicio >= fin:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Horario invalido',
            description='El inicio del intervalo debe ser anterior al fin'
        ))
    duracion = (fin - inicio).total_seconds() / 3600
    if not DURACION_MIN_HORAS <= duracion <= DURACION_MAX_HORAS:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Duracion invalida',
            description=f'La duracion debe ser entre {DURACION_MIN_HORAS} y {DURACION_MAX_HORAS} horas'
        ))
    if inicio.hour < HORA_APERTURA or fin.hour * 60 + fin.minute > HORA_CIERRE * 60:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Fuera del horario del club',
            description=f'El club atiende de {HORA_APERTURA:02d}:00 a {HORA_CIERRE:02d}:00'
        ))
    ahora = datetime.now(timezone.utc).astimezone(GMT_MENOS_3).replace(tzinfo=None)
    if inicio <= ahora:
        raise ValueError(construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Horario no futuro',
            description='El intervalo debe ser posterior al momento actual'
        ))