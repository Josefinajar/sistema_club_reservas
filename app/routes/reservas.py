import logging
from urllib.parse import urlencode

from flask import Blueprint, jsonify, request

from app.services import reserva_service
from app.utils import construir_error_api
from app.validators.reservas_validator import (
    ErrorReserva,
    validar_estado,
    validar_filtros,
    validar_paginacion,
    validar_reserva_nueva,
)

logger = logging.getLogger(__name__)

reservas_bp = Blueprint('reservas', __name__)


@reservas_bp.errorhandler(ErrorReserva)
def manejar_error_reserva(error: ErrorReserva):
    return jsonify(error.payload), error.status


@reservas_bp.errorhandler(Exception)
def manejar_error_inesperado(error: Exception):
    logger.exception(error)
    return jsonify(construir_error_api(
        code='internal.error',
        message='Error interno del servidor',
        description='Ocurrió un error inesperado al procesar la solicitud',
    )), 500


def _link(offset: int, limit: int) -> dict:
    parametros = {k: v for k, v in request.args.items() if k not in ('_limit', '_offset')}
    parametros.update({'_offset': offset, '_limit': limit})
    return {'href': f'{request.base_url}?{urlencode(parametros)}'}


def _links_paginacion(total: int, limit: int, offset: int) -> dict:
    ultimo_offset = ((total - 1) // limit) * limit if total > 0 else 0
    links = {'_first': _link(0, limit)}
    if offset > 0:
        links['_prev'] = _link(max(offset - limit, 0), limit)
    if offset + limit < total:
        links['_next'] = _link(offset + limit, limit)
    links['_last'] = _link(ultimo_offset, limit)
    return links


@reservas_bp.route('/reservas', methods=['GET'])
def get_reservas():
    filtros = validar_filtros(request.args)
    limit, offset = validar_paginacion(request.args)
    reservas, total = reserva_service.listar_reservas(filtros, limit, offset)

    if not reservas:
        return '', 204

    return jsonify({'reservas': reservas, '_links': _links_paginacion(total, limit, offset)}), 200


@reservas_bp.route('/reservas', methods=['POST'])
def post_reserva():
    datos = validar_reserva_nueva(request.get_json(silent=True))
    return jsonify(reserva_service.crear_reserva(datos)), 201


@reservas_bp.route('/reservas/<int:id_reserva>', methods=['GET'])
def get_reserva(id_reserva: int):
    return jsonify(reserva_service.obtener_reserva(id_reserva)), 200


@reservas_bp.route('/reservas/<int:id_reserva>/estado', methods=['PUT'])
def put_estado_reserva(id_reserva: int):
    estado = validar_estado(request.get_json(silent=True))
    return jsonify(reserva_service.cambiar_estado(id_reserva, estado)), 200
