"""
CAPA 0 · RUTAS HTTP
Solo recibe el pedido, llama a validaciones y servicio, y devuelve la respuesta.
Nada de SQL ni de reglas acá.
"""
from flask import Blueprint, jsonify, request

from paginacion import armar_respuesta, leer_paginacion

from . import servicio
from .validaciones import validar_cuerpo_estado, validar_cuerpo_reserva, validar_filtros_listado

reservas_bp = Blueprint("reservas", __name__)


@reservas_bp.get("/reservas")
def listar():
    filtros = validar_filtros_listado(request.args)
    limit, offset = leer_paginacion(request.args)
    items, total = servicio.listar_reservas(filtros, limit, offset)
    return jsonify(armar_respuesta("reservas", items, total, limit, offset)), 200


@reservas_bp.post("/reservas")
def crear():
    datos = validar_cuerpo_reserva(request.get_json(silent=True))
    return jsonify(servicio.crear_reserva(datos)), 201


@reservas_bp.get("/reservas/<int:id_reserva>")
def obtener(id_reserva):
    return jsonify(servicio.obtener_reserva(id_reserva)), 200


@reservas_bp.put("/reservas/<int:id_reserva>/estado")
def cambiar_estado(id_reserva):
    estado = validar_cuerpo_estado(request.get_json(silent=True))
    return jsonify(servicio.cambiar_estado(id_reserva, estado)), 200
