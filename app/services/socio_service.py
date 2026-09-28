from urllib.parse import urlencode
from app.utils import construir_error_api
from app.queries import socios_queries
from app.constants import ERROR_CODE_SOCIO_NOT_FOUND, ERROR_CODE_SOCIO_EXISTS


def listar_socios(limit: int, offset: int, filtros: dict, args_originales: dict, base_url: str) -> dict:

    socios = socios_queries.obtener_socios(filtros, limit, offset)
    total_registros = socios_queries.contar_socios(filtros)

    for socio in socios:
        socio['activo'] = bool(socio['activo'])

    def crear_url(nuevo_offset: int) -> str:
        params = args_originales.copy()
        params['_limit'] = limit
        params['_offset'] = nuevo_offset
        return f"{base_url}?{urlencode(params)}"

    _first = 0
    _prev = max(0, offset - limit)
    _last = max(0, ((total_registros - 1) // limit) * limit) if total_registros > 0 else 0
    _next = offset + limit if (offset + limit) < total_registros else _last

    return {
        "socios": socios,
        "_links": {
            "_first": {"href": crear_url(_first)},
            "_prev": {"href": crear_url(_prev)},
            "_next": {"href": crear_url(_next)},
            "_last": {"href": crear_url(_last)}
        }
    }


def obtener_socio_por_id(id_socio: int) -> dict:
    socio = socios_queries.obtener_socio_por_id(id_socio)

    if not socio:
        raise ValueError((construir_error_api(
            code=ERROR_CODE_SOCIO_NOT_FOUND,
            message='Socio no encontrado',
            description=f"No existe un socio con el ID {id_socio}."
        ), 404))

    return socio


def crear_socio(nombre: str, email: str) -> dict:
    """Verifica duplicado de email y crea el socio."""
    if socios_queries.existe_email(email):
        raise ValueError((construir_error_api(
            code=ERROR_CODE_SOCIO_EXISTS,
            message='Email ya registrado',
            description=f"Ya existe un socio con el email '{email}'"
        ), 409))

    socio = socios_queries.crear_socio(nombre, email)
    socio['activo'] = bool(socio['activo'])
    return socio


def actualizar_socio(id_socio: int, campos: dict) -> dict:
    """Verifica que el socio exista, verifica duplicado de email si corresponde, y actualiza."""
    if not socios_queries.obtener_socio_por_id(id_socio):
        raise ValueError((construir_error_api(
            code=ERROR_CODE_SOCIO_NOT_FOUND,
            message='Socio no encontrado',
            description=f"No existe un socio con el ID {id_socio}."
        ), 404))

    if 'email' in campos and socios_queries.existe_email(campos['email'], excluir_id=id_socio):
        raise ValueError((construir_error_api(
            code=ERROR_CODE_SOCIO_EXISTS,
            message='Email ya registrado',
            description=f"Ya existe un socio con el email '{campos['email']}'"
        ), 409))

    socio = socios_queries.modificar_socio(id_socio, campos)
    socio['activo'] = bool(socio['activo'])
    return socio