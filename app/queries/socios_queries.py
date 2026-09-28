from app.db import ejecutar_consulta, ejecutar_mutacion


def _construir_filtros(filtros: dict) -> tuple[str, dict]:
    """Helper interno para construir la cláusula WHERE dinámicamente."""
    condiciones = []
    parametros = {}

    if 'nombre' in filtros:
        condiciones.append("LOWER(nombre) LIKE LOWER(:nombre)")
        parametros['nombre'] = f"%{filtros['nombre']}%"

    if 'activo' in filtros:
        condiciones.append("activo = :activo")
        parametros['activo'] = filtros['activo']

    where_clause = " WHERE " + " AND ".join(condiciones) if condiciones else ""
    return where_clause, parametros


def obtener_socios(filtros: dict, limite: int, offset: int) -> list[dict]:
    """Obtiene el listado de socios aplicando filtros y paginación."""
    where_clause, parametros = _construir_filtros(filtros)

    sql = f"SELECT id, nombre, email, activo FROM socios{where_clause} ORDER BY id ASC LIMIT :limit OFFSET :offset"
    parametros['limit'] = limite
    parametros['offset'] = offset

    return ejecutar_consulta(sql, parametros)


def contar_socios(filtros: dict) -> int:
    """Cuenta el total de socios que coinciden con los filtros (para HATEOAS)."""
    where_clause, parametros = _construir_filtros(filtros)

    sql = f"SELECT COUNT(*) as total FROM socios{where_clause}"
    resultado = ejecutar_consulta(sql, parametros)
    return resultado[0]['total'] if resultado else 0


def obtener_socio_por_id(id_socio: int) -> dict | None:
    """Obtiene el socio filtrando por id."""
    sql = "SELECT id, nombre, email, activo FROM socios WHERE id = :id"
    resultados = ejecutar_consulta(sql, {"id": id_socio})

    if not resultados:
        return None

    socio = resultados[0]
    socio['activo'] = bool(socio['activo'])
    return socio


def existe_email(email: str, excluir_id: int = None) -> bool:
    """Retorna True si ya existe un socio con ese email (case-insensitive).
    Si se pasa excluir_id, ignora al socio con ese id (util para PATCH)."""
    if excluir_id is not None:
        sql = "SELECT id FROM socios WHERE LOWER(email) = LOWER(:email) AND id != :excluir_id"
        parametros = {"email": email, "excluir_id": excluir_id}
    else:
        sql = "SELECT id FROM socios WHERE LOWER(email) = LOWER(:email)"
        parametros = {"email": email}

    return len(ejecutar_consulta(sql, parametros)) > 0


def crear_socio(nombre: str, email: str) -> dict:
    """Inserta un nuevo socio (activo = True por defecto) y retorna el socio creado."""
    sql = "INSERT INTO socios (nombre, email, activo) VALUES (:nombre, :email, 1)"
    nuevo_id = ejecutar_mutacion(sql, {"nombre": nombre, "email": email})

    return obtener_socio_por_id(nuevo_id)


def modificar_socio(id_socio: int, campos: dict) -> dict:
    """Actualiza los campos recibidos del socio con el id dado."""
    set_clause = ", ".join(f"{campo} = :{campo}" for campo in campos)
    sql = f"UPDATE socios SET {set_clause} WHERE id = :id"
    parametros = {**campos, "id": id_socio}

    ejecutar_mutacion(sql, parametros)

    return obtener_socio_por_id(id_socio)