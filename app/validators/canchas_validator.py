from datetime import datetime
import re

from app.constants import ERROR_CODE_INVALID_BODY, MIN_ID
from app.utils import (
	construir_error_api,
	validar_bool,
	validar_bool_query,
	validar_entero_query,
	validar_intervalo_club,
	validar_minimo,
	validar_string_no_vacio,
)


CAMPOS_ALTA = {'nombre', 'id_deporte', 'precio_hora', 'techada', 'activa'}
CAMPOS_UPDATE = {'nombre', 'precio_hora', 'techada', 'activa'}


def _rechazar_desconocidos(datos, permitidos: set) -> None:
	desconocidos = set(datos.keys()) - permitidos
	if desconocidos:
		raise ValueError(construir_error_api(
			code=ERROR_CODE_INVALID_BODY,
			message='Campos desconocidos',
			description=f"Campos no permitidos: {', '.join(sorted(desconocidos))}",
		))


def _obtener_errores(error: ValueError) -> list[dict]:
	return error.args[0]['errors']


def _validar_entero_json(valor, nombre: str) -> int:
	if isinstance(valor, bool) or not isinstance(valor, int):
		raise ValueError(construir_error_api(
			code=f'invalid.{nombre}.format',
			message=f"Formato de '{nombre}' invalido",
			description=f"El campo '{nombre}' debe ser un numero entero",
		))
	return valor


def _validar_nombre_cancha(valor) -> str:
	if not isinstance(valor, str):
		raise ValueError(construir_error_api(
			code='invalid.nombre.format',
			message="Formato de 'nombre' invalido",
			description="El campo 'nombre' debe ser un texto",
		))
	return validar_string_no_vacio(valor, 'nombre')


def validar_body_nueva_cancha(body) -> dict:
	if not isinstance(body, dict):
		raise ValueError(construir_error_api(
			code=ERROR_CODE_INVALID_BODY,
			message='Cuerpo de la solicitud invalido',
			description='El cuerpo debe ser un JSON valido con Content-Type application/json',
		))

	_rechazar_desconocidos(body, CAMPOS_ALTA)
	errores = []
	resultado = {'techada': False, 'activa': True}
	validadores = (
		('nombre', lambda: _validar_nombre_cancha(body.get('nombre'))),
		('id_deporte', lambda: validar_minimo(_validar_entero_json(body.get('id_deporte'), 'id_deporte'), MIN_ID, 'id_deporte')),
		('precio_hora', lambda: validar_minimo(_validar_entero_json(body.get('precio_hora'), 'precio_hora'), 1, 'precio_hora')),
	)
	for campo, validar in validadores:
		try:
			resultado[campo] = validar()
		except ValueError as error:
			errores.extend(_obtener_errores(error))

	for campo in ('techada', 'activa'):
		if campo in body:
			try:
				resultado[campo] = validar_bool(body[campo], campo)
			except ValueError as error:
				errores.extend(_obtener_errores(error))
	if errores:
		raise ValueError({'errors': errores})
	return resultado


def validar_body_actualizar_cancha(body) -> dict:
	if not isinstance(body, dict) or not body:
		raise ValueError(construir_error_api(
			code=ERROR_CODE_INVALID_BODY,
			message='Cuerpo de la solicitud invalido',
			description='El cuerpo de la actualizacion no puede estar vacio',
		))

	_rechazar_desconocidos(body, CAMPOS_UPDATE)
	errores = []
	resultado = {}
	if 'nombre' in body:
		try:
			resultado['nombre'] = _validar_nombre_cancha(body['nombre'])
		except ValueError as error:
			errores.extend(_obtener_errores(error))
	if 'precio_hora' in body:
		try:
			precio = _validar_entero_json(body['precio_hora'], 'precio_hora')
			resultado['precio_hora'] = validar_minimo(precio, 1, 'precio_hora')
		except ValueError as error:
			errores.extend(_obtener_errores(error))
	for campo in ('techada', 'activa'):
		if campo in body:
			try:
				resultado[campo] = validar_bool(body[campo], campo)
			except ValueError as error:
				errores.extend(_obtener_errores(error))
	if errores:
		raise ValueError({'errors': errores})
	return resultado


def validar_query_listado(args) -> dict:
	permitidos = {'id_deporte', 'nombre', 'techada', 'activa', '_limit', '_offset'}
	_rechazar_desconocidos(args, permitidos)
	filtros = {}
	if 'id_deporte' in args:
		filtros['id_deporte'] = validar_entero_query(args['id_deporte'], 'id_deporte')
	if 'nombre' in args:
		filtros['nombre'] = args['nombre']
	for campo in ('techada', 'activa'):
		if campo in args:
			filtros[campo] = validar_bool_query(args[campo], campo)
	return filtros


def validar_query_disponibilidad(args) -> tuple[datetime, datetime, dict]:
	permitidos = {'fecha', 'hora_inicio', 'hora_fin', 'id_deporte', 'techada', '_limit', '_offset'}
	_rechazar_desconocidos(args, permitidos)
	for campo in ('fecha', 'hora_inicio', 'hora_fin'):
		if campo not in args:
			raise ValueError(construir_error_api(
				code=ERROR_CODE_INVALID_BODY,
				message=f"Falta el parametro '{campo}'",
				description=f"El parametro '{campo}' es obligatorio",
			))
	try:
		fecha = args['fecha']
		hora_inicio = args['hora_inicio']
		hora_fin = args['hora_fin']
		if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', fecha):
			raise ValueError
		if not re.fullmatch(r'(?:[01]\d|2[0-3]):00:00', hora_inicio):
			raise ValueError
		if not re.fullmatch(r'(?:[01]\d|2[0-3]):00:00', hora_fin):
			raise ValueError
		inicio = datetime.strptime(f'{fecha} {hora_inicio}', '%Y-%m-%d %H:%M:%S')
		fin = datetime.strptime(f'{fecha} {hora_fin}', '%Y-%m-%d %H:%M:%S')
	except ValueError:
		raise ValueError(construir_error_api(
			code=ERROR_CODE_INVALID_BODY,
			message='Fecha u hora invalida',
			description="'fecha' debe ser YYYY-MM-DD y 'hora_inicio'/'hora_fin' deben ser HH:00:00",
		))
	validar_intervalo_club(inicio, fin)
	filtros = {}
	if 'id_deporte' in args:
		filtros['id_deporte'] = validar_entero_query(args['id_deporte'], 'id_deporte')
	if 'techada' in args:
		filtros['techada'] = validar_bool_query(args['techada'], 'techada')
	return inicio, fin, filtros
