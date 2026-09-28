from app.constants import ERROR_CODE_CANCHA_NOT_FOUND, ERROR_CODE_CONFLICT, ERROR_CODE_DEPORTE_NOT_FOUND
from app.queries import canchas_queries
from app.utils import construir_error_api, parse_pagination
from app.validators.canchas_validator import (
	validar_body_actualizar_cancha,
	validar_body_nueva_cancha,
	validar_query_disponibilidad,
	validar_query_listado,
)


def listar_canchas(query_args) -> tuple[list[dict], int, int, int]:
	limit, offset = parse_pagination(query_args)
	filtros = validar_query_listado(query_args)
	total = canchas_queries.contar_canchas(filtros)
	return canchas_queries.listar_canchas(filtros, limit, offset), total, limit, offset


def buscar_cancha_por_id(id_cancha: int) -> dict:
	return canchas_queries.obtener_cancha_por_id(id_cancha)


def crear_cancha(body) -> dict:
	datos = validar_body_nueva_cancha(body)
	if not canchas_queries.existe_deporte(datos['id_deporte']):
		raise ValueError(construir_error_api(
			code=ERROR_CODE_DEPORTE_NOT_FOUND,
			message='Deporte no encontrado',
			description=f"No existe un deporte con id '{datos['id_deporte']}'",
		), 404)
	nuevo_id = canchas_queries.insertar_cancha(
		datos['nombre'], datos['id_deporte'], datos['precio_hora'], datos['techada'], datos['activa']
	)
	return canchas_queries.obtener_cancha_por_id(nuevo_id)


def actualizar_cancha(id_cancha: int, body) -> dict:
	if not canchas_queries.obtener_cancha_por_id(id_cancha):
		raise ValueError(construir_error_api(
			code=ERROR_CODE_CANCHA_NOT_FOUND,
			message='Cancha no encontrada',
			description=f"No existe una cancha con id '{id_cancha}'",
		), 404)
	campos = validar_body_actualizar_cancha(body)
	canchas_queries.actualizar_cancha(id_cancha, campos)
	return canchas_queries.obtener_cancha_por_id(id_cancha)


def eliminar_cancha(id_cancha: int) -> None:
	resultado = canchas_queries.eliminar_cancha(id_cancha)
	if resultado == 'not_found':
		raise ValueError(construir_error_api(
			code=ERROR_CODE_CANCHA_NOT_FOUND,
			message='Cancha no encontrada',
			description=f"No existe una cancha con id '{id_cancha}'",
		), 404)
	if resultado == 'has_reservations':
		raise ValueError(construir_error_api(
			code=ERROR_CODE_CONFLICT,
			message='No se puede eliminar la cancha',
			description='La cancha tiene reservas asociadas; puede desactivarla mediante PATCH',
		), 409)


def listar_canchas_disponibles(query_args) -> tuple[list[dict], int, int, int]:
	limit, offset = parse_pagination(query_args)
	inicio, fin, filtros = validar_query_disponibilidad(query_args)
	total = canchas_queries.contar_canchas_disponibles(filtros, inicio, fin)
	canchas = canchas_queries.listar_canchas_disponibles(filtros, inicio, fin, limit, offset)
	return canchas, total, limit, offset
