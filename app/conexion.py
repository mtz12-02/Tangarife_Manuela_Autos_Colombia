# Importar las herramientas necesarias para conectar con PostgreSQL
import os
import psycopg
from dotenv import load_dotenv

# Cargar las variables guardadas en el archivo .env
load_dotenv()


def obtener_conexion():
    # Obtener los datos de conexión desde el archivo .env
    host = os.getenv("DB_HOST", "localhost")
    puerto = os.getenv("DB_PORT", "5432")
    base_datos = os.getenv("DB_NAME", "autos_colombia")
    usuario = os.getenv("DB_USER", "postgres")
    contrasena = os.getenv("DB_PASSWORD")

    # Comprobar que la contraseña esté configurada
    if not contrasena:
        raise ValueError("Falta configurar DB_PASSWORD en el archivo .env")

    # Conectar con la base de datos
    return psycopg.connect(
        host=host,
        port=puerto,
        dbname=base_datos,
        user=usuario,
        password=contrasena
    )
