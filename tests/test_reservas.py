from datetime import timedelta

import pytest

from conftest import fecha_hora, reserva
from app.validators.reservas_validator import ahora

URL = '/api/reservas'


def cantidad_reservas(sql) -> int:
    return sql('SELECT COUNT(*) AS n FROM reservas')[0]['n']


def codigo_error(respuesta) -> str:
    return respuesta.get_json()['errors'][0]['code']


# ---------------------------------------------------------------
# Creación e importes
# ---------------------------------------------------------------

def test_crear_reserva_valida(cliente):
    r = cliente.post(URL, json=reserva(desde=18, hasta=20))
    assert r.status_code == 201
    datos = r.get_json()
    assert datos['id'] == 1
    assert datos['estado'] == 'confirmada'
    assert datos['precio_hora'] == 1000000
    assert datos['precio_total'] == 2000000
    assert datos['fecha_hora_inicio'] == reserva()['fecha_hora_inicio']


def test_conserva_tarifa_historica(cliente, sql):
    id_reserva = cliente.post(URL, json=reserva()).get_json()['id']
    sql('UPDATE canchas SET precio_hora = 5000000 WHERE id = 1')
    datos = cliente.get(f'{URL}/{id_reserva}').get_json()
    assert datos['precio_hora'] == 1000000
    assert datos['precio_total'] == 2000000


@pytest.mark.parametrize('extra', [{'estado': 'cancelada'}, {'precio_total': 1}, {'precio_hora': 1}, {'id': 99}])
def test_rechaza_campos_generados_por_el_servidor(cliente, sql, extra):
    r = cliente.post(URL, json={**reserva(), **extra})
    assert r.status_code == 400
    assert cantidad_reservas(sql) == 0


# ---------------------------------------------------------------
# Superposiciones
# ---------------------------------------------------------------

@pytest.mark.parametrize('desde, hasta', [
    (19, 21),  # parcial
    (18, 20),  # idéntica
    (18, 19),  # contenida
    (17, 20),  # contenedora
])
def test_rechaza_superposicion_de_cancha(cliente, sql, desde, hasta):
    assert cliente.post(URL, json=reserva(id_socio=1, desde=18, hasta=20)).status_code == 201
    r = cliente.post(URL, json=reserva(id_socio=2, desde=desde, hasta=hasta))
    assert r.status_code == 409
    assert codigo_error(r) == 'reserva.overlap.cancha'
    assert cantidad_reservas(sql) == 1


def test_rechaza_superposicion_de_socio_en_otra_cancha(cliente, sql):
    assert cliente.post(URL, json=reserva(id_cancha=1, desde=18, hasta=20)).status_code == 201
    r = cliente.post(URL, json=reserva(id_cancha=2, desde=19, hasta=20))
    assert r.status_code == 409
    assert codigo_error(r) == 'reserva.overlap.socio'
    assert cantidad_reservas(sql) == 1


def test_acepta_reservas_consecutivas(cliente):
    assert cliente.post(URL, json=reserva(desde=18, hasta=20)).status_code == 201
    assert cliente.post(URL, json=reserva(desde=20, hasta=21)).status_code == 201
    assert cliente.post(URL, json=reserva(desde=16, hasta=18)).status_code == 201


# ---------------------------------------------------------------
# Horarios inválidos
# ---------------------------------------------------------------

@pytest.mark.parametrize('inicio, fin', [
    (fecha_hora(1, 7), fecha_hora(1, 9)),       # antes de la apertura
    (fecha_hora(1, 22), fecha_hora(2, 0)),      # atraviesa la medianoche
    (fecha_hora(1, 10), fecha_hora(1, 14)),     # más de 3 horas
    (fecha_hora(1, 10), fecha_hora(1, 10)),     # duración cero
    (fecha_hora(1, 12), fecha_hora(1, 10)),     # fin anterior al inicio
    (fecha_hora(1, 10).replace(':00:00.', ':30:00.'), fecha_hora(1, 12)),  # no es hora en punto
    (fecha_hora(-1, 10), fecha_hora(-1, 12)),   # en el pasado
    ('2026-10-15 18:00', fecha_hora(1, 12)),    # formato incorrecto
    (fecha_hora(1, 10).replace('-03:00', '-05:00'), fecha_hora(1, 12)),  # otra zona horaria
])
def test_rechaza_horarios_invalidos(cliente, sql, inicio, fin):
    r = cliente.post(URL, json={'id_socio': 1, 'id_cancha': 1,
                                'fecha_hora_inicio': inicio, 'fecha_hora_fin': fin})
    assert r.status_code == 400
    assert cantidad_reservas(sql) == 0


def test_acepta_ultimo_turno_hasta_las_23(cliente):
    assert cliente.post(URL, json=reserva(desde=20, hasta=23)).status_code == 201


# ---------------------------------------------------------------
# Referencias inexistentes, entidades inactivas y cuerpos inválidos
# ---------------------------------------------------------------

@pytest.mark.parametrize('id_socio, id_cancha, status, codigo', [
    (99, 1, 404, 'socio.not.found'),
    (1, 99, 404, 'cancha.not.found'),
    (3, 1, 409, 'socio.inactive'),
    (1, 3, 409, 'cancha.inactive'),
])
def test_rechaza_socio_o_cancha_invalidos(cliente, sql, id_socio, id_cancha, status, codigo):
    r = cliente.post(URL, json=reserva(id_socio=id_socio, id_cancha=id_cancha))
    assert r.status_code == status
    assert codigo_error(r) == codigo
    assert cantidad_reservas(sql) == 0


@pytest.mark.parametrize('cuerpo', [
    None,
    {},
    [1, 2],
    {'id_socio': 1, 'id_cancha': 1, 'fecha_hora_inicio': fecha_hora(1, 18)},
    {**reserva(), 'id_socio': '1'},
    {**reserva(), 'id_socio': True},
    {**reserva(), 'id_cancha': -2},
])
def test_rechaza_cuerpos_invalidos(cliente, sql, cuerpo):
    r = cliente.post(URL, json=cuerpo) if cuerpo is not None else cliente.post(URL)
    assert r.status_code == 400
    assert set(r.get_json()['errors'][0]) == {'code', 'message', 'level', 'description'}
    assert cantidad_reservas(sql) == 0


# ---------------------------------------------------------------
# Estados
# ---------------------------------------------------------------

def test_cancelar_libera_el_horario(cliente):
    id_reserva = cliente.post(URL, json=reserva()).get_json()['id']
    r = cliente.put(f'{URL}/{id_reserva}/estado', json={'estado': 'cancelada'})
    assert r.status_code == 200
    assert r.get_json()['estado'] == 'cancelada'
    assert cliente.get(f'{URL}/{id_reserva}').get_json()['estado'] == 'cancelada'
    assert cliente.post(URL, json=reserva()).status_code == 201


def test_repetir_estado_actual_no_modifica(cliente):
    id_reserva = cliente.post(URL, json=reserva()).get_json()['id']
    r = cliente.put(f'{URL}/{id_reserva}/estado', json={'estado': 'confirmada'})
    assert r.status_code == 200
    assert r.get_json()['estado'] == 'confirmada'
    cliente.put(f'{URL}/{id_reserva}/estado', json={'estado': 'cancelada'})
    r = cliente.put(f'{URL}/{id_reserva}/estado', json={'estado': 'cancelada'})
    assert r.status_code == 200


def test_cancelada_no_cambia_de_estado(cliente):
    id_reserva = cliente.post(URL, json=reserva()).get_json()['id']
    cliente.put(f'{URL}/{id_reserva}/estado', json={'estado': 'cancelada'})
    for estado in ('confirmada', 'finalizada'):
        r = cliente.put(f'{URL}/{id_reserva}/estado', json={'estado': estado})
        assert r.status_code == 409
        assert codigo_error(r) == 'reserva.invalid.transition'


def test_no_finaliza_antes_de_terminar(cliente):
    id_reserva = cliente.post(URL, json=reserva()).get_json()['id']
    r = cliente.put(f'{URL}/{id_reserva}/estado', json={'estado': 'finalizada'})
    assert r.status_code == 409


def _insertar_reserva_pasada(sql) -> int:
    inicio = (ahora() - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    sql("""INSERT INTO reservas (id_socio, id_cancha, fecha_hora_inicio, fecha_hora_fin,
                                 estado, tarifa_historica, total)
           VALUES (1, 1, %s, %s, 'confirmada', 1000000, 1000000)""",
        (inicio, inicio + timedelta(hours=1)))
    return sql('SELECT MAX(id) AS id FROM reservas')[0]['id']


def test_finaliza_reserva_terminada(cliente, sql):
    id_reserva = _insertar_reserva_pasada(sql)
    r = cliente.put(f'{URL}/{id_reserva}/estado', json={'estado': 'finalizada'})
    assert r.status_code == 200
    assert r.get_json()['estado'] == 'finalizada'
    r = cliente.put(f'{URL}/{id_reserva}/estado', json={'estado': 'cancelada'})
    assert r.status_code == 409


def test_no_cancela_reserva_comenzada(cliente, sql):
    id_reserva = _insertar_reserva_pasada(sql)
    r = cliente.put(f'{URL}/{id_reserva}/estado', json={'estado': 'cancelada'})
    assert r.status_code == 409


@pytest.mark.parametrize('cuerpo', [{'estado': 'pendiente'}, {}, {'estado': 'cancelada', 'x': 1}])
def test_estado_invalido(cliente, cuerpo):
    id_reserva = cliente.post(URL, json=reserva()).get_json()['id']
    assert cliente.put(f'{URL}/{id_reserva}/estado', json=cuerpo).status_code == 400


def test_reserva_inexistente(cliente):
    r = cliente.get(f'{URL}/999')
    assert r.status_code == 404
    assert codigo_error(r) == 'reserva.not.found'
    assert cliente.put(f'{URL}/999/estado', json={'estado': 'cancelada'}).status_code == 404


# ---------------------------------------------------------------
# Listado: filtros y paginación
# ---------------------------------------------------------------

def _cargar_varias(cliente):
    cliente.post(URL, json=reserva(id_socio=1, id_cancha=1, dia=1, desde=8, hasta=9))    # id 1
    cliente.post(URL, json=reserva(id_socio=2, id_cancha=1, dia=1, desde=9, hasta=10))   # id 2
    cliente.post(URL, json=reserva(id_socio=1, id_cancha=1, dia=2, desde=8, hasta=9))    # id 3
    cliente.post(URL, json=reserva(id_socio=1, id_cancha=2, dia=3, desde=8, hasta=9))    # id 4
    cliente.post(URL, json=reserva(id_socio=1, id_cancha=1, dia=3, desde=10, hasta=11))  # id 5
    cliente.put(f'{URL}/5/estado', json={'estado': 'cancelada'})


def ids(respuesta) -> list[int]:
    return [r['id'] for r in respuesta.get_json()['reservas']]


def test_listado_con_paginacion(cliente):
    _cargar_varias(cliente)
    r = cliente.get(f'{URL}?_limit=2&_offset=2')
    assert r.status_code == 200
    assert ids(r) == [3, 4]
    links = r.get_json()['_links']
    assert '_offset=0' in links['_first']['href']
    assert '_offset=0' in links['_prev']['href']
    assert '_offset=4' in links['_next']['href']
    assert '_offset=4' in links['_last']['href']


def test_listado_combina_filtros_y_paginacion(cliente):
    _cargar_varias(cliente)
    r = cliente.get(f'{URL}?id_socio=1&id_cancha=1&estado=confirmada&_limit=1')
    assert ids(r) == [1]
    links = r.get_json()['_links']
    assert 'id_socio=1' in links['_next']['href']
    assert '_offset=1' in links['_last']['href']  # ids 1 y 3 cumplen los filtros
    assert '_prev' not in links


def test_listado_filtra_por_rango_de_fechas(cliente):
    _cargar_varias(cliente)
    dia_2 = (ahora() + timedelta(days=2)).date().isoformat()
    dia_3 = (ahora() + timedelta(days=3)).date().isoformat()
    assert ids(cliente.get(f'{URL}?fecha_desde={dia_2}&fecha_hasta={dia_3}')) == [3, 4, 5]
    assert ids(cliente.get(f'{URL}?fecha_hasta={dia_2}')) == [1, 2, 3]


def test_listado_vacio_devuelve_204(cliente):
    assert cliente.get(URL).status_code == 204


@pytest.mark.parametrize('query', [
    '?fecha_desde=2026-12-10&fecha_hasta=2026-12-01',
    '?color=rojo',
    '?estado=pendiente',
    '?id_socio=abc',
    '?id_socio=0',
    '?fecha_desde=10/12/2026',
    '?_limit=0',
    '?_limit=101',
    '?_offset=-1',
])
def test_listado_rechaza_parametros_invalidos(cliente, query):
    assert cliente.get(f'{URL}{query}').status_code == 400
