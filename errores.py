"""
Error "controlado" de la API.

Cuando algo está mal (dato inválido, reserva que no existe, horario ocupado...)
se lanza un ErrorApi con un mensaje y un código HTTP. app.py lo atrapa y lo
devuelve al cliente como JSON: {"error": "mensaje"}.
"""


class ErrorApi(Exception):
    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
