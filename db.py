"""
Conexión a MySQL.

>>> PROBABLEMENTE SE REEMPLACE POR LA DEL GRUPO <<<
Si tus compañeros ya tienen su propia forma de conectarse, borrás este archivo
y en reservas/servicio.py cambiás el import de obtener_conexion por el de ellos.

Se abre una conexión por cada request y se cierra al terminar.
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
