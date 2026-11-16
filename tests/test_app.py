
# Importar las herramientas necesarias para las pruebas
import os
import sys
from pathlib import Path

import pytest

# Ubicar la carpeta de la aplicación
CARPETA_PROYECTO = Path(__file__).resolve().parent.parent
CARPETA_APP = CARPETA_PROYECTO / "app"

# Permitir importar los archivos de la aplicación
sys.path.insert(0, str(CARPETA_APP))

# Configurar una clave para ejecutar las pruebas
os.environ["FLASK_SECRET_KEY"] = "clave-de-prueba"

# Importar la aplicación
import app as modulo_app


# Preparar la aplicación para las pruebas
@pytest.fixture
def cliente():
    modulo_app.app.config["TESTING"] = True

    with modulo_app.app.test_client() as cliente:
        yield cliente


# Comprobar que se muestra el formulario de registro
def test_mostrar_formulario_registro(cliente):
    respuesta = cliente.get("/registrar")

    assert respuesta.status_code == 200
    assert "Registrar vehículo" in respuesta.get_data(as_text=True)


# Comprobar que no se registra un vehículo sin placa
def test_registro_sin_placa(cliente, monkeypatch):
    def registro_falso(*args):
        pytest.fail("No debería registrar un vehículo sin placa")

    monkeypatch.setattr(modulo_app, "registrar_vehiculo", registro_falso)

    respuesta = cliente.post("/registrar", data={"placa": ""})

    assert respuesta.status_code == 302


# Comprobar que se registra un vehículo correctamente
def test_registrar_vehiculo(cliente, monkeypatch):
    datos = {}

    def registro_falso(placa, marca, modelo, color):
        datos["placa"] = placa
        datos["marca"] = marca
        datos["modelo"] = modelo
        datos["color"] = color

    monkeypatch.setattr(modulo_app, "registrar_vehiculo", registro_falso)

    respuesta = cliente.post(
        "/registrar",
        data={
            "placa": "abc123",
            "marca": "Chevrolet",
            "modelo": "Spark",
            "color": "Gris"
        }
    )

    assert respuesta.status_code == 302
    assert datos["placa"] == "ABC123"
    assert datos["marca"] == "Chevrolet"


# Comprobar que se rechaza una entrada sin vehículo válido
def test_entrada_sin_vehiculo(cliente, monkeypatch):
    def entrada_falsa(id_vehiculo):
        pytest.fail("No debería registrar una entrada inválida")

    monkeypatch.setattr(modulo_app, "registrar_entrada", entrada_falsa)

    respuesta = cliente.post("/entrada", data={"id_vehiculo": ""})

    assert respuesta.status_code == 302


# Comprobar que se registra una salida correctamente
def test_registrar_salida(cliente, monkeypatch):
    datos = {}

    def salida_falsa(id_movimiento):
        datos["id_movimiento"] = id_movimiento
        return True

    monkeypatch.setattr(modulo_app, "registrar_salida", salida_falsa)

    respuesta = cliente.post(
        "/salida",
        data={"id_movimiento": "5"}
    )

    assert respuesta.status_code == 302
    assert datos["id_movimiento"] == 5


# Comprobar que no se guarda una novedad vacía
def test_novedad_sin_descripcion(cliente, monkeypatch):
    def novedad_falsa(*args):
        pytest.fail("No debería guardar una novedad vacía")

    monkeypatch.setattr(modulo_app, "registrar_novedad", novedad_falsa)

    respuesta = cliente.post(
        "/novedades",
        data={
            "id_movimiento": "1",
            "descripcion": ""
        }
    )

    assert respuesta.status_code == 302


# Comprobar que se puede consultar el historial
def test_consultar_historial(cliente, monkeypatch):
    monkeypatch.setattr(modulo_app, "obtener_historial", lambda: [])

    respuesta = cliente.get("/historial")

    assert respuesta.status_code == 200
    assert b"Historial de movimientos" in respuesta.data
