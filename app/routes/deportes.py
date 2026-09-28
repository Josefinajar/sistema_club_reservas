from flask import Blueprint, jsonify
from app.services import deporte_service

deportes_bp = Blueprint('deportes', __name__)

@deportes_bp.route('/deportes', methods=['GET'])
def get_deportes():
    deportes = deporte_service.listar_deportes()
    
    if not deportes:
        return '', 204
        
    return jsonify({"deportes": deportes}), 200