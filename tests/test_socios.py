from flask import Flask

from app.constants import BASE_URL
from app.routes import socios as socios_routes
from app.routes.socios import socios_bp
from app.validators.socios_validator import validar_body_crear_socio, validar_email


def test_validar_body_crear_socio_normaliza_nombre_y_email():
	datos = validar_body_crear_socio({'nombre': '  Juan Perez  ', 'email': 'Juan.Perez@TEST.com'})

	assert datos == {
		'nombre': 'Juan Perez',
		'email': 'juan.perez@test.com',
	}


def test_validar_body_crear_socio_rechaza_nombre_vacio():
	try:
		validar_body_crear_socio({'nombre': '   ', 'email': 'juan@test.com'})
	except ValueError as error:
		assert error.args[0][0]['errors'][0]['code'] == 'invalid.body'
	else:
		raise AssertionError('Se esperaba error para nombre vacio')


def test_validar_email_rechaza_sin_arroba():
	try:
		validar_email('juanattest.com')
	except ValueError as error:
		assert error.args[0][0]['errors'][0]['message'] == 'Email invalido'
	else:
		raise AssertionError('Se esperaba error para email sin @')


def test_post_socio_crea_correctamente(monkeypatch):
	socio_creado = {'id': 1, 'nombre': 'Juan Perez', 'email': 'juan.perez@test.com', 'activo': True}
	monkeypatch.setattr(socios_routes.socio_service, 'crear_socio', lambda nombre, email: socio_creado)

	app = Flask(__name__)
	app.register_blueprint(socios_bp, url_prefix=BASE_URL)
	client = app.test_client()

	respuesta = client.post('/api/socios', json={'nombre': 'Juan Perez', 'email': 'juan.perez@test.com'})

	assert respuesta.status_code == 201
	assert respuesta.json == socio_creado
