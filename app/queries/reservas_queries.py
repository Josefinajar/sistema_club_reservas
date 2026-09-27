from datetime import timedelta

from sqlalchemy import text

from app.db import ejecutar_consulta, fila_a_dict

SELECT_RESERVA = """
    SELECT id, id_socio, id_cancha, fecha_hora_inicio, fecha_hora_fin, estado,
           tarifa_historica AS precio_hora, total AS precio_total
    FROM reservas
"""


def _una_fila(conexion, sql: str, parametros: dict) -> dict | None:
    fila = conexion.execute(text(sql), parametros).first()
    return fila_a_dict(fila) if fila else None


# Las siguientes funciones reciben una conexión abierta para ejecutarse dentro
# de la transacción del servicio. FOR UPDATE bloquea la fila hasta el commit,
# así dos pedidos simultáneos sobre la misma cancha o socio no se pisan.

def bloquear_socio(conexion, id_socio: int) -> dict | None:
    sql = 'SELECT id, activo FROM socios WHERE id = :id FOR UPDATE'
    return _una_fila(conexion, sql, {'id': id_socio})


def bloquear_cancha(conexion, id_cancha: int) -> dict | None:
    sql = 'SELECT id, activa, precio_hora FROM canchas WHERE id = :id FOR UPDATE'
    return _una_fila(conexion, sql, {'id': id_cancha})


def existe_superposicion(conexion, columna: str, id_valor: int, inicio, fin) -> bool:
    """
    Busca reservas confirmadas que se superpongan con [inicio, fin).
    Dos intervalos se superponen si inicio_existente < fin_nuevo
    y inicio_nuevo < fin_existente.
    """
    if columna not in ('id_cancha', 'id_socio'):
        raise ValueError(f'Columna no permitida: {columna}')
    sql = f"""
        SELECT 1 FROM reservas
        WHERE {columna} = :id AND estado = 'confirmada'
          AND fecha_hora_inicio < :fin AND :inicio < fecha_hora_fin
        LIMIT 1
    """
    return _una_fila(conexion, sql, {'id': id_valor, 'inicio': inicio, 'fin': fin}) is not None


def insertar_reserva(conexion, id_socio: int, id_cancha: int, inicio, fin,
                     precio_hora: int, precio_total: int) -> int:
    sql = """
        INSERT INTO reservas (id_socio, id_cancha, fecha_hora_inicio, fecha_hora_fin,
                              estado, tarifa_historica, total)
        VALUES (:id_socio, :id_cancha, :inicio, :fin, 'confirmada', :precio_hora, :precio_total)
    """
    resultado = conexion.execute(text(sql), {
        'id_socio': id_socio, 'id_cancha': id_cancha, 'inicio': inicio, 'fin': fin,
        'precio_hora': precio_hora, 'precio_total': precio_total,
    })
    return resultado.lastrowid


def obtener_reserva(conexion, id_reserva: int, bloquear: bool = False) -> dict | None:
    sql = SELECT_RESERVA + ' WHERE id = :id' + (' FOR UPDATE' if bloquear else '')
    return _una_fila(conexion, sql, {'id': id_reserva})


def actualizar_estado(conexion, id_reserva: int, estado: str) -> None:
    sql = 'UPDATE reservas SET estado = :estado WHERE id = :id'
    conexion.execute(text(sql), {'estado': estado, 'id': id_reserva})


# Consultas de solo lectura, sin transacción.

def obtener_reserva_por_id(id_reserva: int) -> dict | None:
    filas = ejecutar_consulta(SELECT_RESERVA + ' WHERE id = :id', {'id': id_reserva})
    return filas[0] if filas else None


def listar_reservas(filtros: dict, limit: int, offset: int) -> tuple[list[dict], int]:
    """Devuelve la página pedida y el total de reservas que cumplen los filtros."""
    condiciones, parametros = [], {}
    for campo in ('id_cancha', 'id_socio', 'estado'):
        if campo in filtros:
            condiciones.append(f'{campo} = :{campo}')
            parametros[campo] = filtros[campo]
    # El rango se aplica al día de uso de la cancha, con ambos extremos incluidos
    if 'fecha_desde' in filtros:
        condiciones.append('fecha_hora_inicio >= :fecha_desde')
        parametros['fecha_desde'] = filtros['fecha_desde']
    if 'fecha_hasta' in filtros:
        condiciones.append('fecha_hora_inicio < :fecha_hasta')
        parametros['fecha_hasta'] = filtros['fecha_hasta'] + timedelta(days=1)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ''

    total = ejecutar_consulta(f'SELECT COUNT(*) AS total FROM reservas {where}', parametros)[0]['total']
    reservas = ejecutar_consulta(
        f'{SELECT_RESERVA} {where} ORDER BY id LIMIT :limit OFFSET :offset',
        {**parametros, 'limit': limit, 'offset': offset},
    )
    return reservas, total
