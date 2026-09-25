"""
Conexión a MySQL.

"""
import pymysql
import pymysql.cursors
from flask import current_app, g


def obtener_conexion():
    if "db" not in g:
        g.db = pymysql.connect(
            **current_app.config["CONFIG_DB"],
            cursorclass=pymysql.cursors.DictCursor,  # las filas vuelven como diccionarios
            autocommit=False,  # confirmamos a mano con commit(), así nada queda a medias
        )
    return g.db


def cerrar_conexion(_error=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()
