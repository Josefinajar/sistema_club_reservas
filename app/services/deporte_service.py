from app.queries import deportes_queries

def listar_deportes() -> list[dict]:
    """Devuelve el listado de deportes obtenidos de la base de datos."""
    return deportes_queries.obtener_todos_los_deportes()