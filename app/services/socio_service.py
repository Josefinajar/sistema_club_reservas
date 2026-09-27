from urllib.parse import urlencode
from app.utils import construir_error_api
from app.queries import socios_queries

def listar_socios(limit: int, offset: int, filtros: dict, args_originales: dict, base_url: str) -> dict:
    
    # 1. Consultar a la base de datos
    socios = socios_queries.obtener_socios(filtros, limit, offset)
    total_registros = socios_queries.contar_socios(filtros)

    # 2. Formatear la respuesta (asegurar que activo sea boolean en JSON y no 1/0)
    for socio in socios:
        socio['activo'] = bool(socio['activo'])

    # 3. Construir enlaces HATEOAS
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
            code='not_found',
            message='Socio no encontrado',
            description=f"No existe un socio con el ID {id_socio}."
        ), 404))
        
    return socio