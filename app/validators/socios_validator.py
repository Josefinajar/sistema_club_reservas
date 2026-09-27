from app.utils import construir_error_api

def validar_parametros_get_socios(args: dict) -> dict:
    """Valida los parámetros de la consulta GET /socios y devuelve los filtros limpios."""
    
    # 1. Rechazar parámetros desconocidos
    parametros_permitidos = {'_limit', '_offset', 'nombre', 'activo'}
    for param in args.keys():
        if param not in parametros_permitidos:
            raise ValueError((construir_error_api(
                code='invalid.parameter',
                message='Parámetro desconocido',
                description=f"El parámetro '{param}' no está permitido."
            ), 400))

    # 2. Validar _limit y _offset
    try:
        limit = int(args.get('_limit', 5))
        if not (1 <= limit <= 100):
            raise ValueError()
    except ValueError:
        raise ValueError((construir_error_api(
            code='invalid.limit', message='Límite inválido', description='_limit debe ser un entero entre 1 y 100.'
        ), 400))

    try:
        offset = int(args.get('_offset', 0))
        if offset < 0:
            raise ValueError()
    except ValueError:
        raise ValueError((construir_error_api(
            code='invalid.offset', message='Offset inválido', description='_offset debe ser un entero mayor o igual a 0.'
        ), 400))

    # 3. Validar y parsear filtros
    filtros = {}
    if 'nombre' in args:
        filtros['nombre'] = args['nombre']
    
    if 'activo' in args:
        valor_activo = args['activo'].lower()
        if valor_activo not in ['true', 'false']:
            raise ValueError((construir_error_api(
                code='invalid.activo', message='Filtro inválido', description="El filtro 'activo' solo admite 'true' o 'false'."
            ), 400))
        filtros['activo'] = True if valor_activo == 'true' else False

    return {'limit': limit, 'offset': offset, 'filtros': filtros}