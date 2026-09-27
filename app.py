import logging
from flask import Flask

# Importamos la constante BASE_URL
from app.constants import BASE_URL

# Importamos los blueprints de cada ruta
from app.routes.canchas import canchas_bp
from app.routes.deportes import deportes_bp
from app.routes.reservas import reservas_bp
from app.routes.socios import socios_bp

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

app = Flask(__name__)
app.json.sort_keys = False

# Registramos los blueprints
app.register_blueprint(canchas_bp, url_prefix=BASE_URL)
app.register_blueprint(deportes_bp, url_prefix=BASE_URL)
app.register_blueprint(reservas_bp, url_prefix=BASE_URL)
app.register_blueprint(socios_bp, url_prefix=BASE_URL)

if __name__ == '__main__':
    app.run(debug=True, port=5000)