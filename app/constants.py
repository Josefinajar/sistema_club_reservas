import os
from dotenv import load_dotenv

load_dotenv()

# URL base de la API
BASE_URL = '/api'

# Reglas de dominio
MIN_ID = 1
HORA_APERTURA = 8
HORA_CIERRE = 23
DURACION_MIN_HORAS = 1
DURACION_MAX_HORAS = 3

# Paginacion
LIMIT_DEFAULT = 10
LIMIT_MIN = 1
LIMIT_MAX = 100
OFFSET_DEFAULT = 0

# Configuracion de la base de datos MySQL (levantada via docker-compose)
DB_HOST     = os.getenv('DB_HOST', 'localhost')
DB_PORT     = int(os.getenv('DB_PORT', '3306'))
DB_USER     = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME     = os.getenv('DB_NAME', 'club_deportivo')
DB_URL      = f'mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Codigos de error genericos
ERROR_CODE_INVALID_BODY      = 'invalid.body'
ERROR_CODE_INVALID_MIN_VALUE = 'invalid.min.value'
ERROR_CODE_CONFLICT          = 'conflict'

# Codigos de error para CANCHAS
ERROR_CODE_CANCHA_NOT_FOUND  = 'cancha.not.found'
ERROR_CODE_CANCHA_EXISTS     = 'cancha.already.exists'

# Codigos de error para DEPORTES
ERROR_CODE_DEPORTE_NOT_FOUND = 'deporte.not.found'
ERROR_CODE_DEPORTE_EXISTS    = 'deporte.already.exists'

# Codigos de error para RESERVAS
ERROR_CODE_RESERVA_NOT_FOUND = 'reserva.not.found'
ERROR_CODE_RESERVA_EXISTS    = 'reserva.already.exists'

# Codigos de error para SOCIOS
ERROR_CODE_SOCIO_NOT_FOUND   = 'socio.not.found'
ERROR_CODE_SOCIO_EXISTS      = 'socio.already.exists'