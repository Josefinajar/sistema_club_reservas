from flask import Blueprint, jsonify, request
from app.services import socio_service
from app.validators.socios_validator import (
    validar_id,
    validar_parametros_get_socios,
    validar_body_crear_socio,
    validar_body_actualizar_socio
)

socios_bp = Blueprint('socios', __name__)


@socios_bp.route('/socios', methods=['GET'])
def get_socios():
    args = request.args.to_dict()
    base_url = request.base_url

    try:
        datos_validados = validar_parametros_get_socios(args)
    except ValueError as e:
        error_payload, status_code = e.args[0]
        return jsonify(error_payload), status_code

    resultado = socio_service.listar_socios(
        limit=datos_validados['limit'],
        offset=datos_validados['offset'],
        filtros=datos_validados['filtros'],
        args_originales=args,
        base_url=base_url
    )

    if not resultado['socios']:
        return '', 204

    return jsonify(resultado), 200


@socios_bp.route('/socios/<id>', methods=['GET'])
def get_socio_by_id(id):
    try:
        id_validado = validar_id(id)
        socio = socio_service.obtener_socio_por_id(id_validado)
    except ValueError as e:
        error_payload, status_code = e.args[0]
        return jsonify(error_payload), status_code

    return jsonify(socio), 200


@socios_bp.route('/socios', methods=['POST'])
def post_socio():
    body = request.get_json()

    try:
        datos_validados = validar_body_crear_socio(body)
        socio_nuevo = socio_service.crear_socio(datos_validados['nombre'], datos_validados['email'])
    except ValueError as e:
        error_payload, status_code = e.args[0]
        return jsonify(error_payload), status_code

    return jsonify(socio_nuevo), 201


@socios_bp.route('/socios/<id>', methods=['PATCH'])
def patch_socio(id):
    body = request.get_json()

    try:
        id_validado = validar_id(id)
        campos_validados = validar_body_actualizar_socio(body)
        socio_actualizado = socio_service.actualizar_socio(id_validado, campos_validados)
    except ValueError as e:
        error_payload, status_code = e.args[0]
        return jsonify(error_payload), status_code

    return jsonify(socio_actualizado)