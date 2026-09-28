from sqlalchemy import text

from app.db import ejecutar_consulta, ejecutar_mutacion, obtener_conexion


def existe_deporte(id_deporte: int) -> bool:
	filas = ejecutar_consulta('SELECT 1 FROM deportes WHERE id = :id_deporte', {'id_deporte': id_deporte})
	return bool(filas)


def _cancha_a_dict(fila: dict) -> dict:
	return {
		'id': fila['id'],
		'nombre': fila['nombre'],
		'id_deporte': fila['id_deporte'],
		'precio_hora': fila['precio_hora'],
		'techada': bool(fila['techada']),
		'activa': bool(fila['activa']),
	}


def _where_canchas(filtros: dict, alias: str = '') -> tuple[str, dict]:
	clausulas = []
	parametros = {}
	prefijo = f'{alias}.' if alias else ''
	for campo in ('id_deporte', 'techada', 'activa'):
		if filtros.get(campo) is not None:
			clausulas.append(f'{prefijo}{campo} = :{campo}')
			parametros[campo] = filtros[campo]
	if filtros.get('nombre') is not None:
		clausulas.append(f'LOWER({prefijo}nombre) LIKE :nombre')
		parametros['nombre'] = f"%{filtros['nombre'].lower()}%"
	return (' AND '.join(clausulas), parametros)


def contar_canchas(filtros: dict) -> int:
	where, parametros = _where_canchas(filtros)
	sql = f'SELECT COUNT(*) AS total FROM canchas' + (f' WHERE {where}' if where else '')
	return ejecutar_consulta(sql, parametros)[0]['total']


def listar_canchas(filtros: dict, limit: int, offset: int) -> list[dict]:
	where, parametros = _where_canchas(filtros)
	sql = (
		'SELECT id, nombre, id_deporte, precio_hora, techada, activa FROM canchas'
		+ (f' WHERE {where}' if where else '')
		+ ' ORDER BY id ASC LIMIT :limit OFFSET :offset'
	)
	parametros.update({'limit': limit, 'offset': offset})
	return [_cancha_a_dict(fila) for fila in ejecutar_consulta(sql, parametros)]


def obtener_cancha_por_id(id_cancha: int) -> dict:
	sql = 'SELECT id, nombre, id_deporte, precio_hora, techada, activa FROM canchas WHERE id = :id_cancha'
	filas = ejecutar_consulta(sql, {'id_cancha': id_cancha})
	return _cancha_a_dict(filas[0]) if filas else {}


def insertar_cancha(nombre: str, id_deporte: int, precio_hora: int, techada: bool, activa: bool) -> int:
	sql = (
		'INSERT INTO canchas (nombre, id_deporte, precio_hora, techada, activa) '
		'VALUES (:nombre, :id_deporte, :precio_hora, :techada, :activa)'
	)
	return ejecutar_mutacion(sql, {
		'nombre': nombre,
		'id_deporte': id_deporte,
		'precio_hora': precio_hora,
		'techada': techada,
		'activa': activa,
	})


def actualizar_cancha(id_cancha: int, campos: dict) -> None:
	if not campos:
		return
	permitidos = {'nombre', 'precio_hora', 'techada', 'activa'}
	if not set(campos).issubset(permitidos):
		raise ValueError('Campo de actualizacion no permitido')
	asignaciones = ', '.join(f'{campo} = :{campo}' for campo in campos)
	parametros = dict(campos)
	parametros['id_cancha'] = id_cancha
	ejecutar_mutacion(f'UPDATE canchas SET {asignaciones} WHERE id = :id_cancha', parametros)


def eliminar_cancha(id_cancha: int) -> str:
	with obtener_conexion() as conexion:
		with conexion.begin():
			cancha = conexion.execute(
				text('SELECT id FROM canchas WHERE id = :id_cancha FOR UPDATE'),
				{'id_cancha': id_cancha},
			).first()
			if cancha is None:
				return 'not_found'

			reserva = conexion.execute(
				text('SELECT 1 FROM reservas WHERE id_cancha = :id_cancha LIMIT 1'),
				{'id_cancha': id_cancha},
			).first()
			if reserva is not None:
				return 'has_reservations'

			conexion.execute(
				text('DELETE FROM canchas WHERE id = :id_cancha'),
				{'id_cancha': id_cancha},
			)
			return 'deleted'


def cancha_tiene_reservas(id_cancha: int) -> bool:
	filas = ejecutar_consulta(
		'SELECT 1 FROM reservas WHERE id_cancha = :id_cancha LIMIT 1',
		{'id_cancha': id_cancha},
	)
	return bool(filas)


_SIN_SUPERPOSICION = (
	'NOT EXISTS ('
	' SELECT 1 FROM reservas r WHERE r.id_cancha = c.id'
	" AND r.estado = 'confirmada'"
	' AND r.fecha_hora_inicio < :fecha_fin AND :fecha_inicio < r.fecha_hora_fin'
	')'
)


def _where_canchas_disponibles(filtros: dict) -> tuple[str, dict]:
	clausulas = ['c.activa = 1']
	where_filtros, parametros = _where_canchas(filtros, 'c')
	if where_filtros:
		clausulas.append(where_filtros)
	return ' AND '.join(clausulas), parametros


def contar_canchas_disponibles(filtros: dict, inicio, fin) -> int:
	where, parametros = _where_canchas_disponibles(filtros)
	parametros.update({'fecha_fin': fin, 'fecha_inicio': inicio})
	sql = f'SELECT COUNT(*) AS total FROM canchas c WHERE {where} AND {_SIN_SUPERPOSICION}'
	return ejecutar_consulta(sql, parametros)[0]['total']


def listar_canchas_disponibles(filtros: dict, inicio, fin, limit: int, offset: int) -> list[dict]:
	where, parametros = _where_canchas_disponibles(filtros)
	parametros.update({'fecha_fin': fin, 'fecha_inicio': inicio, 'limit': limit, 'offset': offset})
	sql = (
		'SELECT c.id, c.nombre, c.id_deporte, c.precio_hora, c.techada, c.activa '
		f'FROM canchas c WHERE {where} AND {_SIN_SUPERPOSICION} '
		'ORDER BY c.id ASC LIMIT :limit OFFSET :offset'
	)
	return [_cancha_a_dict(fila) for fila in ejecutar_consulta(sql, parametros)]
