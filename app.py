"""
Punto de entrada de la aplicación.

>>> ESTE ARCHIVO ES PROVISORIO <<<
Seguramente llevar al de ellos son las dos líneas marcadas con "RESERVAS".
"""
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from config import CONFIG_DB
from db import cerrar_conexion
from errores import ErrorApi
from reservas.rutas import reservas_bp  # RESERVAS (1/2)


def crear_app(config_db=None):
    app = Flask(__name__)
    app.config["CONFIG_DB"] = config_db or CONFIG_DB
    app.json.sort_keys = False  # respeta el orden de los campos en las respuestas

    app.register_blueprint(reservas_bp)  # RESERVAS (2/2)
    app.teardown_appcontext(cerrar_conexion)

    # Todos los errores salen como JSON: {"error": "..."}
    @app.errorhandler(ErrorApi)
    def error_api(error):
        return jsonify({"error": error.mensaje}), error.codigo

    mensajes = {404: "Recurso no encontrado", 405: "Método no permitido"}

    @app.errorhandler(HTTPException)
    def error_http(error):
        return jsonify({"error": mensajes.get(error.code, error.name)}), error.code

    @app.errorhandler(Exception)
    def error_inesperado(error):
        app.logger.exception(error)
        return jsonify({"error": "Error interno del servidor"}), 500

    return app


if __name__ == "__main__":
    crear_app().run(debug=True, port=5000)
