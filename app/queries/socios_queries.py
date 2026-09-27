from app.db import ejecutar_consulta

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
    socio['activo'] = bool(socio['activo']) # Aseguramos que sea boolean puro
    return socio