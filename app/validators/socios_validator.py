from app.utils import construir_error_api, validar_minimo
from app.constants import ERROR_CODE_INVALID_BODY, MIN_ID


def validar_id(id_raw) -> int:
    """Valida que el id recibido sea un entero mayor o igual a MIN_ID."""
    try:
        id_convertido = int(id_raw)
    except (ValueError, TypeError):
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Id invalido',
            description=f"El id '{id_raw}' no puede convertirse a un numero entero"
        ), 400))

    try:
        return validar_minimo(id_convertido, MIN_ID, 'id')
    except ValueError as e:
        raise ValueError((e.args[0], 400))


def validar_parametros_get_socios(args: dict) -> dict:
    """Valida los parámetros de la consulta GET /socios y devuelve los filtros limpios."""

    # 1. Rechazar parámetros desconocidos
    parametros_permitidos = {'_limit', '_offset', 'nombre', 'activo'}
    for param in args.keys():
        if param not in parametros_permitidos:
            raise ValueError((construir_error_api(
                code=ERROR_CODE_INVALID_BODY,
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
            code=ERROR_CODE_INVALID_BODY, message='Límite inválido', description='_limit debe ser un entero entre 1 y 100.'
        ), 400))

    try:
        offset = int(args.get('_offset', 0))
        if offset < 0:
            raise ValueError()
    except ValueError:
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY, message='Offset inválido', description='_offset debe ser un entero mayor o igual a 0.'
        ), 400))

    # 3. Validar y parsear filtros
    filtros = {}
    if 'nombre' in args:
        filtros['nombre'] = args['nombre']

    if 'activo' in args:
        valor_activo = args['activo'].lower()
        if valor_activo not in ['true', 'false']:
            raise ValueError((construir_error_api(
                code=ERROR_CODE_INVALID_BODY, message='Filtro inválido', description="El filtro 'activo' solo admite 'true' o 'false'."
            ), 400))
        filtros['activo'] = True if valor_activo == 'true' else False

    return {'limit': limit, 'offset': offset, 'filtros': filtros}


def validar_email(email: str) -> str:
    """Valida el formato de un email. Retorna el email en minusculas si es valido."""
    if not email or "@" not in email:
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Email invalido',
            description='El email debe contener un @'
        ), 400))

    partes = email.split("@")

    if len(partes) != 2:
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Email invalido',
            description='El email debe tener un solo @'
        ), 400))

    usuario, dominio = partes

    if usuario == "" or not all(c.isalnum() or c in "-_." for c in usuario):
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Email invalido',
            description='El nombre de usuario del email es invalido'
        ), 400))

    if "." not in dominio or not dominio[0].isalpha() or not dominio[-1].isalpha():
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Email invalido',
            description='El dominio del email es invalido'
        ), 400))

    for parte in dominio.split("."):
        if parte == "" or not parte.isalnum():
            raise ValueError((construir_error_api(
                code=ERROR_CODE_INVALID_BODY,
                message='Email invalido',
                description=f"Parte de dominio invalida: '{parte}'"
            ), 400))

    return email.lower()


def validar_body_crear_socio(body: dict) -> dict:
    """Valida el body del POST /socios. Retorna {'nombre': ..., 'email': ...}."""
    if not body:
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Cuerpo invalido',
            description='Debe enviar los datos del nuevo socio'
        ), 400))

    nombre = body.get('nombre')
    if not nombre or not str(nombre).strip():
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Nombre invalido',
            description='El nombre no puede estar vacio'
        ), 400))

    email = body.get('email')
    if not email:
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Email invalido',
            description='El email es obligatorio'
        ), 400))

    email_validado = validar_email(email)

    return {'nombre': str(nombre).strip(), 'email': email_validado}


def validar_body_actualizar_socio(body: dict) -> dict:
    """Valida el body del PATCH /socios/<id>. Retorna solo los campos validos a actualizar."""
    if not body:
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Cuerpo invalido',
            description='Debe enviar al menos un campo para actualizar'
        ), 400))

    campos_a_actualizar = {}

    if 'nombre' in body:
        nombre = body['nombre']
        if not nombre or not str(nombre).strip():
            raise ValueError((construir_error_api(
                code=ERROR_CODE_INVALID_BODY,
                message='Nombre invalido',
                description='El nombre no puede estar vacio'
            ), 400))
        campos_a_actualizar['nombre'] = str(nombre).strip()

    if 'email' in body:
        campos_a_actualizar['email'] = validar_email(body['email'])

    if 'activo' in body:
        activo = body['activo']
        if not isinstance(activo, bool):
            raise ValueError((construir_error_api(
                code=ERROR_CODE_INVALID_BODY,
                message='Formato invalido',
                description="El campo 'activo' debe ser true o false"
            ), 400))
        campos_a_actualizar['activo'] = activo

    if not campos_a_actualizar:
        raise ValueError((construir_error_api(
            code=ERROR_CODE_INVALID_BODY,
            message='Cuerpo invalido',
            description='Ningun campo valido para actualizar fue enviado'
        ), 400))

    return campos_a_actualizar