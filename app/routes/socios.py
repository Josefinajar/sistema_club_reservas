from flask import Blueprint, jsonify, request
from app.services import socio_service
from app.validators.socios_validator import validar_parametros_get_socios

socios_bp = Blueprint('socios', __name__)

@socios_bp.route('/socios', methods=['GET'])
def get_socios():
    args = request.args.to_dict()
    base_url = request.base_url 

    # Capa 1: Validación
    try:
        datos_validados = validar_parametros_get_socios(args)
    except ValueError as e:
        error_payload, status_code = e.args[0]
        return jsonify(error_payload), status_code

    # Capa 2: Reglas de negocio
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

@socios_bp.route('/socios/<int:id>', methods=['GET'])
def get_socio_by_id(id):
    try:
        socio = socio_service.obtener_socio_por_id(id)
        return jsonify(socio), 200
    except ValueError as e:
        error_payload, status_code = e.args[0]
        return jsonify(error_payload), status_code