"""
CAPA 1 · VALIDACIONES
Revisa que lo que manda el cliente tenga sentido. Acá NO se toca la base de datos.
Si algo está mal, lanza ErrorApi (400).
"""
import re
from datetime import date, datetime, timedelta, timezone

from errores import ErrorApi

ZONA_ARGENTINA = timezone(timedelta(hours=-3))
FORMATO_FECHA_HORA = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}-03:00$")
FORMATO_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FORMATO_ENTERO_POSITIVO = re.compile(r"^[1-9]\d*$")

HORA_APERTURA = 8
HORA_CIERRE = 23
DURACION_MINIMA = 1
DURACION_MAXIMA = 3
ESTADOS = ("confirmada", "cancelada", "finalizada")

CAMPOS_RESERVA = {"id_socio", "id_cancha", "fecha_hora_inicio", "fecha_hora_fin"}
FILTROS_LISTADO = {"id_cancha", "id_socio", "estado", "fecha_desde", "fecha_hasta", "_limit", "_offset"}


def ahora():
    """Momento actual en GMT-3, sin zona horaria (así se guarda en la base)."""
    return datetime.now(ZONA_ARGENTINA).replace(tzinfo=None)


# ---------- valores sueltos ----------

def validar_id(valor, campo):
    # Ojo: en Python True/False también cuentan como int, por eso se excluyen aparte.
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ErrorApi(f"'{campo}' debe ser un entero positivo")
    return valor


def parsear_id_query(texto, campo):
    if not FORMATO_ENTERO_POSITIVO.match(texto):
        raise ErrorApi(f"'{campo}' debe ser un entero positivo")
    return int(texto)


def parsear_fecha_hora(valor, campo):
    """'2026-10-15T18:00:00.000000-03:00' -> datetime(2026, 10, 15, 18, 0)"""
    if not isinstance(valor, str) or not FORMATO_FECHA_HORA.match(valor):
        raise ErrorApi(f"'{campo}' debe tener formato YYYY-MM-DDTHH:MM:SS.ffffff-03:00")
    try:
        return datetime.fromisoformat(valor).replace(tzinfo=None)
    except ValueError:
        raise ErrorApi(f"'{campo}' no es una fecha y hora válida")


def parsear_fecha(texto, campo):
    if not FORMATO_FECHA.match(texto):
        raise ErrorApi(f"'{campo}' debe tener formato YYYY-MM-DD")
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ErrorApi(f"'{campo}' no es una fecha válida")


def validar_intervalo(inicio, fin):
    """Reglas de horario de la sección 3 del enunciado. Devuelve la cantidad de horas."""
    for momento, campo in ((inicio, "fecha_hora_inicio"), (fin, "fecha_hora_fin")):
        if momento.minute or momento.second or momento.microsecond:
            raise ErrorApi(f"'{campo}' debe ser una hora en punto")
    if inicio >= fin:
        raise ErrorApi("fecha_hora_inicio debe ser anterior a fecha_hora_fin")
    if inicio.date() != fin.date():
        raise ErrorApi("La reserva no puede atravesar la medianoche")
    if inicio.hour < HORA_APERTURA or fin.hour > HORA_CIERRE:
        raise ErrorApi("La reserva debe estar dentro del horario del club (08:00 a 23:00)")
    horas = (fin - inicio) // timedelta(hours=1)
    if not DURACION_MINIMA <= horas <= DURACION_MAXIMA:
        raise ErrorApi("La reserva debe durar entre 1 y 3 horas")
    if inicio <= ahora():
        raise ErrorApi("La reserva debe comenzar en el futuro")
    return horas


# ---------- cuerpos JSON ----------

def _exigir_objeto(cuerpo):
    if not isinstance(cuerpo, dict) or not cuerpo:
        raise ErrorApi("El cuerpo debe ser un objeto JSON no vacío")


def validar_cuerpo_reserva(cuerpo):
    _exigir_objeto(cuerpo)
    desconocidos = set(cuerpo) - CAMPOS_RESERVA
    if desconocidos:
        raise ErrorApi(f"Campos no permitidos: {', '.join(sorted(desconocidos))}")
    faltantes = CAMPOS_RESERVA - set(cuerpo)
    if faltantes:
        raise ErrorApi(f"Faltan campos obligatorios: {', '.join(sorted(faltantes))}")
    return {
        "id_socio": validar_id(cuerpo["id_socio"], "id_socio"),
        "id_cancha": validar_id(cuerpo["id_cancha"], "id_cancha"),
        "inicio": parsear_fecha_hora(cuerpo["fecha_hora_inicio"], "fecha_hora_inicio"),
        "fin": parsear_fecha_hora(cuerpo["fecha_hora_fin"], "fecha_hora_fin"),
    }


def validar_cuerpo_estado(cuerpo):
    _exigir_objeto(cuerpo)
    desconocidos = set(cuerpo) - {"estado"}
    if desconocidos:
        raise ErrorApi(f"Campos no permitidos: {', '.join(sorted(desconocidos))}")
    estado = cuerpo.get("estado")
    if estado not in ESTADOS:
        raise ErrorApi(f"'estado' debe ser uno de: {', '.join(ESTADOS)}")
    return estado


# ---------- filtros del listado ----------

def validar_filtros_listado(args):
    """Recibe los parámetros de la URL y devuelve un diccionario con los filtros usados."""
    desconocidos = set(args.keys()) - FILTROS_LISTADO
    if desconocidos:
        raise ErrorApi(f"Parámetros no permitidos: {', '.join(sorted(desconocidos))}")

    filtros = {}
    for campo in ("id_cancha", "id_socio"):
        if campo in args:
            filtros[campo] = parsear_id_query(args[campo], campo)
    if "estado" in args:
        if args["estado"] not in ESTADOS:
            raise ErrorApi(f"'estado' debe ser uno de: {', '.join(ESTADOS)}")
        filtros["estado"] = args["estado"]
    for campo in ("fecha_desde", "fecha_hasta"):
        if campo in args:
            filtros[campo] = parsear_fecha(args[campo], campo)
    if "fecha_desde" in filtros and "fecha_hasta" in filtros:
        if filtros["fecha_desde"] > filtros["fecha_hasta"]:
            raise ErrorApi("fecha_desde debe ser menor o igual a fecha_hasta")
    return filtros
