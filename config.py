"""
Configuración de la base de datos.

Los datos reales (usuario, contraseña) NO se suben al repo: se leen de un
archivo .env (que está en .gitignore). En el repo solo va .env.example.
"""
import os

from dotenv import load_dotenv

load_dotenv()

CONFIG_DB = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "club_deportivo"),
}
