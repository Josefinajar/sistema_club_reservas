from sqlalchemy import create_engine, text
from app.constants import DB_URL

# ---------------------------------------------------------------
# Funciones de soporte genéricas
# ---------------------------------------------------------------

def obtener_conexion():
    """Crea y retorna una nueva conexion a la base de datos."""
    motor = create_engine(DB_URL)
    return motor.connect()

def fila_a_dict(fila) -> dict:
    """Convierte una fila del resultado de una query en un diccionario."""
    return dict(fila._mapping)

def ejecutar_consulta(sql: str, parametros: dict = None) -> list[dict]:
    """Ejecuta una SELECT y devuelve todas las filas como lista de dicts."""
    with obtener_conexion() as conexion:
        resultado = conexion.execute(text(sql), parametros or {})
        return [fila_a_dict(fila) for fila in resultado]

def ejecutar_mutacion(sql: str, parametros: dict = None) -> int:
    """
    Ejecuta un INSERT, UPDATE o DELETE y hace commit.
    Retorna el id autoincremental generado por el INSERT (0 si no aplica).
    """
    with obtener_conexion() as conexion:
        with conexion.begin():
            resultado = conexion.execute(text(sql), parametros or {})
        return resultado.lastrowid or 0