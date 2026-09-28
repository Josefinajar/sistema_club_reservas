from flask import Blueprint, jsonify, request

from app.constants import ERROR_CODE_CANCHA_NOT_FOUND
from app.services.cancha_service import (
	actualizar_cancha,
	buscar_cancha_por_id,
	crear_cancha,
	eliminar_cancha,
	listar_canchas,
	listar_canchas_disponibles,
)
from app.utils import construir_error_api, construir_links


canchas_bp = Blueprint('canchas', __name__)


@canchas_bp.route('/canchas', methods=['GET'])
def get_canchas():
	try:
		canchas, total, limit, offset = listar_canchas(request.args)
	except ValueError as error:
		return jsonify(error.args[0]), error.args[1] if len(error.args) > 1 else 400
	return jsonify({'canchas': canchas, '_links': construir_links(request, total, limit, offset)})


@canchas_bp.route('/canchas', methods=['POST'])
def post_cancha():
	try:
		cancha = crear_cancha(request.get_json(silent=True))
	except ValueError as error:
		return jsonify(error.args[0]), error.args[1] if len(error.args) > 1 else 400
	return jsonify(cancha), 201


@canchas_bp.route('/canchas/disponibles', methods=['GET'])
def get_canchas_disponibles():
	try:
		canchas, total, limit, offset = listar_canchas_disponibles(request.args)
	except ValueError as error:
		return jsonify(error.args[0]), error.args[1] if len(error.args) > 1 else 400
	return jsonify({'canchas': canchas, '_links': construir_links(request, total, limit, offset)})


@canchas_bp.route('/canchas/<int:id_cancha>', methods=['GET'])
def get_cancha(id_cancha):
	cancha = buscar_cancha_por_id(id_cancha)
	if not cancha:
		return jsonify(construir_error_api(
			code=ERROR_CODE_CANCHA_NOT_FOUND,
			message='Cancha no encontrada',
			description=f"No existe una cancha con id '{id_cancha}'",
		)), 404
	return jsonify(cancha)


@canchas_bp.route('/canchas/<int:id_cancha>', methods=['PATCH'])
def patch_cancha(id_cancha):
	try:
		cancha = actualizar_cancha(id_cancha, request.get_json(silent=True))
	except ValueError as error:
		return jsonify(error.args[0]), error.args[1] if len(error.args) > 1 else 400
	return jsonify(cancha)


@canchas_bp.route('/canchas/<int:id_cancha>', methods=['DELETE'])
def delete_cancha(id_cancha):
	try:
		eliminar_cancha(id_cancha)
	except ValueError as error:
		return jsonify(error.args[0]), error.args[1] if len(error.args) > 1 else 400
	return '', 204