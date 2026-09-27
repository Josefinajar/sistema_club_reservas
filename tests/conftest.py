import os
import sys
from datetime import timedelta
from pathlib import Path

import pytest

# La base de pruebas se define antes de importar la app, porque app.constants
# arma la URL de conexión al importarse.
BASE_TEST = 'club_deportivo_test'
os.environ['DB_NAME'] = BASE_TEST

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import mysql.connector  # noqa: E402
from flask import Flask  # noqa: E402

from app.constants import BASE_URL, DB_HOST, DB_PASSWORD, DB_PORT, DB_USER  # noqa: E402
from app.routes.reservas import reservas_bp  # noqa: E402
from app.validators.reservas_validator import ahora  # noqa: E402

# Datos adicionales para las pruebas: se parte sin reservas y se agregan
# una cancha y un socio inactivos (ids 3).
DATOS_PRUEBA = f"""
USE {BASE_TEST};
TRUNCATE TABLE reservas;
INSERT INTO canchas (nombre, id_deporte, precio_hora, techada, activa)
    VALUES ('Cancha inactiva', 1, 600000, FALSE, FALSE);
INSERT INTO socios (nombre, email, activo)
    VALUES ('inactivo', 'inactivo@ejemplo.com', FALSE);
"""


def _conectar(**extra):
    return mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, **extra)


def _recrear_base():
    script = (RAIZ / 'db' / 'init_db.sql').read_text(encoding='utf-8')
    script = script.replace('club_deportivo', BASE_TEST) + DATOS_PRUEBA
    conexion = _conectar()
    try:
        with conexion.cursor() as cursor:
            for sentencia in (s.strip() for s in script.split(';')):
                if sentencia:
                    cursor.execute(sentencia)
        conexion.commit()
    finally:
        conexion.close()


@pytest.fixture
def cliente():
    _recrear_base()
    app = Flask(__name__)
    app.json.sort_keys = False
    app.register_blueprint(reservas_bp, url_prefix=BASE_URL)
    return app.test_client()


@pytest.fixture
def sql():
    """Ejecuta SQL directo sobre la base de pruebas."""
    conexion = _conectar(database=BASE_TEST, autocommit=True)

    def ejecutar(consulta, parametros=()):
        with conexion.cursor(dictionary=True, buffered=True) as cursor:
            cursor.execute(consulta, parametros)
            return cursor.fetchall() if cursor.with_rows else []

    yield ejecutar
    conexion.close()


def fecha_hora(dias: int, hora: int) -> str:
    dia = (ahora() + timedelta(days=dias)).date()
    return f'{dia.isoformat()}T{hora:02d}:00:00.000000-03:00'


def reserva(id_socio=1, id_cancha=1, dia=1, desde=18, hasta=20) -> dict:
    return {
        'id_socio': id_socio,
        'id_cancha': id_cancha,
        'fecha_hora_inicio': fecha_hora(dia, desde),
        'fecha_hora_fin': fecha_hora(dia, hasta),
    }
