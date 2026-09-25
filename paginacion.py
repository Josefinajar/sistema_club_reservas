"""
Paginación con _limit / _offset y enlaces HATEOAS (_first, _prev, _next, _last).

>>> LA USAN TODOS LOS LISTADOS (canchas, socios, reservas) <<<
"""
from urllib.parse import urlencode

from flask import request

from errores import ErrorApi

LIMIT_POR_DEFECTO = 10
LIMIT_MAXIMO = 100


def _entero(texto, campo):
    if not texto.isdigit():
        raise ErrorApi(f"'{campo}' debe ser un entero mayor o igual a cero")
    return int(texto)


def leer_paginacion(args):
    """Lee _limit y _offset de la URL y los valida."""
    limit = _entero(args["_limit"], "_limit") if "_limit" in args else LIMIT_POR_DEFECTO
    offset = _entero(args["_offset"], "_offset") if "_offset" in args else 0
    if not 1 <= limit <= LIMIT_MAXIMO:
        raise ErrorApi(f"'_limit' debe estar entre 1 y {LIMIT_MAXIMO}")
    return limit, offset


def _url(offset, limit):
    """Arma la URL actual conservando los filtros y cambiando solo la página."""
    parametros = {k: v for k, v in request.args.items() if k not in ("_limit", "_offset")}
    parametros["_limit"] = limit
    parametros["_offset"] = offset
    return f"{request.base_url}?{urlencode(parametros)}"


def armar_respuesta(clave, items, total, limit, offset):
    ultimo_offset = ((total - 1) // limit) * limit if total > 0 else 0
    return {
        clave: items,
        "_limit": limit,
        "_offset": offset,
        "_total": total,
        "_links": {
            "_first": _url(0, limit),
            "_prev": _url(max(offset - limit, 0), limit) if offset > 0 else None,
            "_next": _url(offset + limit, limit) if offset + limit < total else None,
            "_last": _url(ultimo_offset, limit),
        },
    }
