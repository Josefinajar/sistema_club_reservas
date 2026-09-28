# Sistema de Reservas de Club Deportivo - API

## Integrantes

|     Nombre     |  Legajo  |
|----------------|----------|
| Casco Jorge    |  116199  |
| Gioda Federico |  116480  |
| Najar Josefina |  113354  |
| Navas Jorge    |  116303  |
| Nieves Alan    |  113133  |

## Arquitectura

```
Cliente HTTP (curl / Postman / Swagger)--
       |
       |  HTTP (JSON)
       v
  Flask API (este proyecto, puerto 5000)
       |
       v
  MySQL (contenedor docker, puerto 3306)
```

## Estructura del proyecto

```
sistema_club_reservas/
├── app.py                          # Entry point Flask (puerto 5000)
├── docker-compose.yml              # MySQL 8 + volumen + datos iniciales
├── requirements.txt                # Dependencias Python
├── swagger.yaml                    # Contrato OpenAPI de la API
├── .env.example                    # Template para configurar la DB
├── .gitignore
├── app/
│   ├── constants.py                # Configuración (DB, BASE_URL y reglas de dominio)
│   ├── db.py                       # Conexión / engine de SQLAlchemy
│   ├── utils.py                    # Funciones reutilizables
│   ├── routes/
│   │   ├── canchas.py              # Endpoints de canchas
│   │   ├── deportes.py             # Endpoints de deportes
│   │   ├── reservas.py             # Endpoints de reservas
│   │   └── socios.py               # Endpoints de socios
│   ├── validators/
│   │   ├── canchas_validator.py    # Validación de entrada para canchas
│   │   ├── reservas_validator.py   # Validación de entrada para reservas
│   │   └── socios_validator.py     # Validación de entrada para socios
│   ├── services/
│   │   ├── cancha_service.py       # Lógica de negocio de canchas
│   │   ├── deporte_service.py      # Lógica de negocio de deportes
│   │   ├── reserva_service.py      # Lógica de negocio de reservas
│   │   └── socio_service.py        # Lógica de negocio de socios
│   └── queries/
│       ├── canchas_queries.py      # SQL literal de canchas
│       ├── deportes_queries.py     # SQL literal de deportes
│       ├── reservas_queries.py     # SQL literal de reservas
│       └── socios_queries.py       # SQL literal de socios
├── db/
│   └── init_db.sql                 # Esquema + deportes iniciales + datos ficticios
└── tests/
    ├── conftest.py                 # Fixtures compartidas
    ├── test_canchas.py
    ├── test_reservas.py
    └── test_socios.py
```

## Documentación (Swagger / OpenAPI)

El contrato completo de la API está en [`swagger.yaml`](swagger.yaml). Se puede visualizar:

- Pegando el contenido en [editor.swagger.io](https://editor.swagger.io).
- Con la extensión "Swagger Viewer" (o similar) en VSCode.
- Con cualquier renderer compatible con OpenAPI 3.

## Requisitos previos

- Python 3.10+
- **Una** de las dos opciones para correr MySQL:
  - Docker + Docker Compose (recomendado), o
  - Una instalación local de MySQL 8

## Instalación y ejecución

Los pasos parten de una copia nueva del repositorio.

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd sistema_club_reservas
```

### 2. Variables de entorno

Copiar `.env.example` a `.env` (**no subir credenciales reales**):

```bash
cp .env.example .env
```

El `docker-compose.yml` lee estas variables y usa los siguientes valores por defecto si no están definidas:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=club_deportivo
```

### 3. Base de datos MySQL

#### Opción A: con Docker (recomendado)

`docker-compose.yml` levanta un contenedor MySQL 8 (`club_reservas_mysql`) y monta `db/init_db.sql` como script de inicialización. La **primera** vez crea las tablas e inserta los deportes iniciales y los datos ficticios. Los datos se guardan en el volumen `mysql_data`, por lo que reiniciar la aplicación o el contenedor **no borra la información**.

```bash
docker compose up -d
```

Verificar que el contenedor esté listo (puede tardar unos segundos):

```bash
docker compose logs -f mysql
# Buscar la línea: "ready for connections"
```

Apagar el contenedor manteniendo los datos:

```bash
docker compose down
```

Apagar y **borrar** los datos (la próxima vez se recargan desde `init_db.sql`):

```bash
docker compose down -v
```

#### Opción B: con MySQL instalado localmente

```bash
# Linux / macOS / WSL
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS club_deportivo;"
mysql -u root -p club_deportivo < db/init_db.sql
```

```powershell
# Windows PowerShell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS club_deportivo;"
Get-Content db\init_db.sql | mysql -u root -p club_deportivo
```

Verificar las tablas:

```bash
mysql -u root -p -e "USE club_deportivo; SHOW TABLES;"
```------------------------------------------

Si tu usuario, password, puerto o nombre de base no coinciden con los defaults, actualizá el `.env`.

### 4. Entorno virtual y dependencias

```bash
python -m venv venv|

# Linux / macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

### 5. Ejecutar la API

```bash
python app.py
```

Una vez iniciada, la API estará disponible en `http://localhost:5000`.

## Endpoints

Las respuestas son JSON. Los listados (salvo `/deportes`) aceptan `_limit` (entre 1 y 100, default 10) y `_offset` (mayor o igual a 0, default 0), se ordenan por `id` ascendente e incluyen un objeto `_links` con `_first`, `_prev`, `_next` y `_last`. Los errores siguen el formato:

```json
{
    "errors": [
        {
            "code": "ERROR_VALIDACION",
            "message": "El cuerpo de la solicitud es inválido",
            "level": "error",
            "description": "El campo 'precio_hora' debe ser un entero mayor a cero"
        }
    ]
}
```

| Método | Endpoint                 | Descripción                                               |
|--------|--------------------------|-----------------------------------------------------------|
| GET    | `/deportes`              | Listar los deportes precargados                           |
| GET    | `/canchas`               | Listar canchas (paginado, con filtros)                    |
| POST   | `/canchas`               | Crear una cancha                                          |
| GET    | `/canchas/disponibles`   | Consultar canchas libres en un intervalo (paginado)       |
| GET    | `/canchas/{id}`          | Obtener una cancha                                        |
| PATCH  | `/canchas/{id}`          | Actualizar parcialmente una cancha                        |
| DELETE | `/canchas/{id}`          | Eliminar una cancha sin reservas asociadas                |
| GET    | `/socios`                | Listar socios (paginado, con filtros)                     |
| POST   | `/socios`                | Registrar un socio                                        |
| GET    | `/socios/{id}`           | Obtener un socio                                          |
| PATCH  | `/socios/{id}`           | Actualizar parcialmente un socio                          |
| GET    | `/reservas`              | Listar reservas (paginado, con filtros)                   |
| POST   | `/reservas`              | Crear una reserva                                         |
| GET    | `/reservas/{id}`         | Obtener una reserva                                       |
| PUT    | `/reservas/{id}/estado`  | Cambiar el estado de una reserva                          |
| GET    | `/bloqueos`              | Listar bloqueos de mantenimiento                          |
| POST   | `/bloqueos`              | Crear un bloqueo de mantenimiento                         |
| DELETE | `/bloqueos/{id}`         | Eliminar un bloqueo                                       |
| POST   | `/reservas/recurrentes`  | Crear una serie de reservas semanales                     |

### Deportes

#### `GET /deportes`

Devuelve los deportes cargados por `init_db.sql`. No tiene paginación.

```bash
curl http://localhost:5000/deportes
```

Respuesta `200 OK`:

```json
{
    "deportes": [
        { "id": 1, "nombre": "Fútbol" }
    ]
}
```

### Canchas

#### `GET /canchas`

Filtros opcionales: `id_deporte`, `nombre` (parcial), `techada`, `activa`. Sin filtros incluye canchas activas e inactivas. Si no hay resultados responde `204 No Content`.

```bash
curl "http://localhost:5000/canchas?id_deporte=1&techada=true&_limit=5&_offset=0"
```

#### `POST /canchas`

| Campo         | Tipo    | Requerido | Descripción                                        |
|---------------|---------|-----------|----------------------------------------------------|
| `nombre`      | string  | sí        | No puede quedar vacío tras quitar espacios         |
| `id_deporte`  | int     | sí        | Debe existir                                       |
| `precio_hora` | int     | sí        | Entero mayor a cero, en centavos                   |
| `techada`     | boolean | no        | Default `false`                                    |
| `activa`      | boolean | no        | Default `true`                                     |

```bash
curl -X POST http://localhost:5000/canchas \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Cancha 1 - Fútbol 5", "id_deporte": 1, "precio_hora": 1000000, "techada": false}'
```

Respuesta `201 Created`. Errores: `400` (datos inválidos), `404` (deporte inexistente).

#### `GET /canchas/{id}`

```bash
curl http://localhost:5000/canchas/1
```

Respuesta `200 OK`:

```json
{
    "id": 1,
    "nombre": "Cancha 1 - Fútbol 5",
    "id_deporte": 1,
    "precio_hora": 1000000,
    "techada": false,
    "activa": true
}
```

Error: `404` (no existe). Que `activa` sea `true` no implica que esté libre en todos los horarios.

#### `PATCH /canchas/{id}`

Campos editables: `nombre`, `precio_hora`, `techada`, `activa`. El deporte no se puede modificar. Cambiar el precio no altera reservas existentes.

```bash
curl -X PATCH http://localhost:5000/canchas/1 \
  -H "Content-Type: application/json" \
  -d '{"precio_hora": 1200000}'
```

Respuesta `204 No Content`. Errores: `400`, `404`.

#### `DELETE /canchas/{id}`

Solo si la cancha no tiene ninguna reserva asociada (sin importar su estado).

```bash
curl -X DELETE http://localhost:5000/canchas/1
```

- `204 No Content`: eliminada.
- `404 Not Found`: no existe.
- `409 Conflict`: tiene reservas; se puede desactivar con `PATCH`.

#### `GET /canchas/disponibles`

Canchas **activas** y libres durante todo el intervalo. Es solo informativa: no crea ni retiene reservas. La habilitación y la agenda del socio se validan al crear la reserva.

| Parámetro     | Requerido | Formato       | Descripción                 |
|---------------|-----------|---------------|-----------------------------|
| `fecha`       | sí        | `YYYY-MM-DD`  | Día a consultar             |
| `hora_inicio` | sí        | `HH:00:00`    | Inicio del intervalo        |
| `hora_fin`    | sí        | `HH:00:00`    | Fin del intervalo           |
| `id_deporte`  | no        | entero        | Filtro por deporte          |
| `techada`     | no        | `true`/`false`| Filtro por techada          |

```bash
curl "http://localhost:5000/canchas/disponibles?fecha=2026-10-15&hora_inicio=18:00:00&hora_fin=20:00:00"
```

El intervalo debe cumplir las mismas reglas que una reserva nueva. Errores: `400` (parámetros faltantes o intervalo inválido).

### Socios

#### `GET /socios`

Filtros opcionales: `nombre` (parcial) y `activo`.

```bash
curl "http://localhost:5000/socios?nombre=juan&activo=true"
```

#### `POST /socios`

| Campo    | Tipo   | Requerido | Descripción                                                    |
|----------|--------|-----------|----------------------------------------------------------------|
| `nombre` | string | sí        | No puede quedar vacío                                          |
| `email`  | string | sí        | Formato válido; se guarda en minúsculas y sin espacios         |

El servidor asigna `activo: true`.

```bash
curl -X POST http://localhost:5000/socios \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Juan Pérez", "email": "juan.perez@example.com"}'
```

Respuesta `201 Created`. Errores: `400` (datos inválidos), `409` (email ya registrado, incluso si el socio está inactivo).

#### `GET /socios/{id}`

```bash
curl http://localhost:5000/socios/1
```

Respuesta `200 OK`:

```json
{
    "id": 1,
    "nombre": "Juan Pérez",
    "email": "juan.perez@example.com",
    "activo": true
}
```

#### `PATCH /socios/{id}`

Actualiza parcialmente `nombre`, `email` o `activo`, con las validaciones del alta y unicidad del correo. No hay endpoint de eliminación de socios.

```bash
curl -X PATCH http://localhost:5000/socios/1 \
  -H "Content-Type: application/json" \
  -d '{"activo": false}'
```

Respuesta `204 No Content`. Errores: `400`, `404`, `409` (email duplicado).

### Reservas

#### `GET /reservas`

Filtros opcionales: `id_cancha`, `id_socio`, `estado` (`confirmada`, `cancelada`, `finalizada`), `fecha_desde`, `fecha_hasta`. El rango se aplica al día de uso de la cancha, ambos extremos incluidos; se puede enviar uno solo y, si se envían los dos, debe cumplirse `fecha_desde <= fecha_hasta`. Permite consultar reservas pasadas.

```bash
curl "http://localhost:5000/reservas?id_cancha=2&estado=confirmada&fecha_desde=2026-10-01&fecha_hasta=2026-10-31"
```

#### `POST /reservas`

| Campo               | Tipo   | Requerido | Descripción                                   |
|---------------------|--------|-----------|-----------------------------------------------|
| `id_socio`          | int    | sí        | Debe existir y estar activo                   |
| `id_cancha`         | int    | sí        | Debe existir y estar activa                   |
| `fecha_hora_inicio` | string | sí        | ISO 8601 con `-03:00`, debe ser futura        |
| `fecha_hora_fin`    | string | sí        | ISO 8601 con `-03:00`                         |

```bash
curl -X POST http://localhost:5000/reservas \
  -H "Content-Type: application/json" \
  -d '{
    "id_socio": 1,
    "id_cancha": 2,
    "fecha_hora_inicio": "2026-10-15T18:00:00.000000-03:00",
    "fecha_hora_fin": "2026-10-15T20:00:00.000000-03:00"
  }'
```

> La fecha del ejemplo es ilustrativa: al probarlo hay que usar una fecha futura.

El servidor asigna el estado `confirmada`, guarda la tarifa vigente y calcula el total (2 horas a `1000000` centavos = `2000000`). Si alguna validación falla no se guarda nada.

Errores: `400` (datos u horarios inválidos, reserva no futura), `404` (socio o cancha inexistente), `409` (superposición de cancha o socio, o entidad inactiva).

#### `GET /reservas/{id}`

Devuelve todos los campos, incluidos estado, tarifa histórica y total.

```bash
curl http://localhost:5000/reservas/1
```

Respuesta `200 OK`:

```json
{
    "id": 1,
    "id_socio": 1,
    "id_cancha": 2,
    "fecha_hora_inicio": "2026-10-15T18:00:00.000000-03:00",
    "fecha_hora_fin": "2026-10-15T20:00:00.000000-03:00",
    "estado": "confirmada",
    "precio_hora": 1000000,
    "precio_total": 2000000
}
```

#### `PUT /reservas/{id}/estado`

```bash
curl -X PUT http://localhost:5000/reservas/1/estado \
  -H "Content-Type: application/json" \
  -d '{"estado": "cancelada"}'
```

- `204 No Content`: estado actualizado (o repetido).
- `400 Bad Request`: estado desconocido.
- `404 Not Found`: la reserva no existe.
- `409 Conflict`: transición no permitida o solicitada fuera del momento permitido.

### Bloqueos

Un bloqueo impide reservar una cancha durante un intervalo y se tiene en cuenta en `GET /canchas/disponibles`. No puede crearse si se superpone con una reserva confirmada o con otro bloqueo de la misma cancha. Debe comenzar en el futuro, quedar dentro de un mismo día, respetar el horario del club y las horas en punto. Puede durar más de tres horas. Eliminar un bloqueo libera solo la restricción que generaba.

#### `POST /bloqueos`

| Campo         | Tipo   | Requerido | Descripción                       |
|---------------|--------|-----------|-----------------------------------|
| `id_cancha`   | int    | sí        | Cancha a bloquear                 |
| `fecha`       | string | sí        | `YYYY-MM-DD`                      |
| `hora_inicio` | string | sí        | `HH:00:00`                        |
| `hora_fin`    | string | sí        | `HH:00:00`                        |
| `motivo`      | string | sí        | Motivo del bloqueo                |

```bash
curl -X POST http://localhost:5000/bloqueos \
  -H "Content-Type: application/json" \
  -d '{
    "id_cancha": 2,
    "fecha": "2026-10-20",
    "hora_inicio": "08:00:00",
    "hora_fin": "12:00:00",
    "motivo": "Mantenimiento de iluminación"
  }'
```

Respuesta `201 Created`. Errores: `400`, `404` (cancha inexistente), `409` (superposición).

#### `GET /bloqueos`

Listado paginado. Filtros opcionales: `id_cancha` y `fecha`.

```bash
curl "http://localhost:5000/bloqueos?id_cancha=2&fecha=2026-10-20"
```

#### `DELETE /bloqueos/{id}`

```bash
curl -X DELETE http://localhost:5000/bloqueos/1
```

Respuesta `204 No Content`. Error: `404`.

### Reservas recurrentes

#### `POST /reservas/recurrentes`

Crea una serie de reservas semanales para la misma cancha, el mismo socio y el mismo intervalo horario. Se valida toda la serie antes de guardar; la operación es completa: si alguna fecha no está disponible, **no se guarda ninguna**.

| Campo               | Tipo   | Requerido | Descripción                                        |
|---------------------|--------|-----------|----------------------------------------------------|
| `id_socio`          | int    | sí        | Debe existir y estar activo                        |
| `id_cancha`         | int    | sí        | Debe existir y estar activa                        |
| `fecha_hora_inicio` | string | sí        | Inicio de la primera reserva (ISO 8601, `-03:00`)  |
| `fecha_hora_fin`    | string | sí        | Fin de la primera reserva                          |
| `cantidad_semanas`  | int    | sí        | Entre 2 y 12, incluyendo la primera                |

```bash
curl -X POST http://localhost:5000/reservas/recurrentes \
  -H "Content-Type: application/json" \
  -d '{
    "id_socio": 1,
    "id_cancha": 2,
    "fecha_hora_inicio": "2026-10-15T18:00:00.000000-03:00",
    "fecha_hora_fin": "2026-10-15T20:00:00.000000-03:00",
    "cantidad_semanas": 4
  }'
```

- `201 Created`: se crearon todas las reservas de la serie.
- `400`: datos inválidos.
- `404`: socio o cancha inexistente.
- `409`: hay fechas en conflicto. La respuesta incluye el detalle en `errors` y las fechas afectadas en `conflictos`:

```json
{
    "errors": [ { "code": "...", "message": "...", "level": "error", "description": "..." } ],
    "conflictos": ["2026-10-22", "2026-11-05"]
}
```

## Patrón de queries literales

Se usa SQLAlchemy **sin ORM**, ejecutando SQL directo con `text()` y siempre con **parámetros** (nunca concatenando datos recibidos):

```python
from sqlalchemy import create_engine, text

motor = create_engine(DB_URL)

# SELECT
with motor.connect() as conexion:
    resultado = conexion.execute(text(sql), {'id': 1})

# INSERT / UPDATE / DELETE (con commit automático)
with motor.begin() as conexion:
    resultado = conexion.execute(text(sql), parametros)
```

Las queries viven en `app/queries/`.
