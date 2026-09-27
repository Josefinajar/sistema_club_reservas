from app.db import ejecutar_consulta

def obtener_todos_los_deportes() -> list[dict]:
    """Obtiene todos los deportes precargados en el sistema."""
    sql = 'SELECT id, nombre FROM deportes ORDER BY id'
    return ejecutar_consulta(sql)