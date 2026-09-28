from flask import Flask

from app.constants import BASE_URL
from app.routes import canchas as canchas_routes
from app.routes.canchas import canchas_bp
from app.validators.canchas_validator import validar_body_nueva_cancha, validar_query_listado


def test_validar_body_nueva_cancha_aplica_defaults():
	datos = validar_body_nueva_cancha({'nombre': 'Cancha 3', 'id_deporte': 1, 'precio_hora': 2500})

	assert datos == {
		'nombre': 'Cancha 3',
		'id_deporte': 1,
		'precio_hora': 2500,
		'techada': False,
		'activa': True,
	}


def test_validar_body_nueva_cancha_rechaza_entero_en_string():
	try:
		validar_body_nueva_cancha({'nombre': 'Cancha 3', 'id_deporte': '1', 'precio_hora': 2500})
	except ValueError as error:
		assert error.args[0]['errors'][0]['code'] == 'invalid.id_deporte.format'
	else:
		raise AssertionError('Se esperaba error para id_deporte no entero')


def test_validar_query_listado_rechaza_booleanos_no_estandar():
	try:
		validar_query_listado({'techada': 'yes'})
	except ValueError as error:
		assert error.args[0]['errors'][0]['code'] == 'invalid.techada.format'
	else:
		raise AssertionError('Se esperaba error para valor booleano inválido')


def test_validar_disponibilidad_rechaza_hora_no_canonica():
	from app.validators.canchas_validator import validar_query_disponibilidad

	try:
		validar_query_disponibilidad({
			'fecha': '2026-10-15',
			'hora_inicio': '8:00:00',
			'hora_fin': '10:00:00',
		})
	except ValueError:
		pass
	else:
		raise AssertionError('Se esperaba error para hora fuera del formato HH:00:00')


def test_get_canchas_devuelve_listado_paginado(monkeypatch):
	monkeypatch.setattr(canchas_routes, 'listar_canchas', lambda args: ([{'id': 1}], 1, 10, 0))
	app = Flask(__name__)
	app.register_blueprint(canchas_bp, url_prefix=BASE_URL)
	client = app.test_client()

	respuesta = client.get('/api/canchas')

	assert respuesta.status_code == 200
	assert respuesta.json['canchas'] == [{'id': 1}]
	assert respuesta.json['_links']['_first']['href'].endswith('_limit=10&_offset=0')
