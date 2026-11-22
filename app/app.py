# Importar las herramientas necesarias para manejar la aplicación
import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash

# Importar las funciones que consultan la base de datos
from consultas import (
    obtener_resumen,
    listar_vehiculos,
    registrar_vehiculo,
    listar_vehiculos_para_entrada,
    registrar_entrada,
    listar_movimientos_activos,
    registrar_salida,
    registrar_novedad,
    obtener_historial,
    listar_usuarios,
    registrar_usuario,
    obtener_usuario,
    actualizar_usuario,
    cambiar_estado_usuario,
    listar_celdas,
    registrar_celda,
    cambiar_estado_celda,
    listar_usuarios_para_pagos,
    registrar_pago,
    obtener_historial_pagos,
    listar_pagos,
    obtener_estado_mensualidades,
    validar_pago,
    eliminar_celda
)

# Cargar las variables de configuración
load_dotenv()

# Preparar el registro de errores
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener la clave secreta desde el archivo .env
clave_secreta = os.getenv("FLASK_SECRET_KEY")

if not clave_secreta:
    raise RuntimeError("Falta configurar FLASK_SECRET_KEY en el archivo .env")

# Crear la aplicación Flask
app = Flask(__name__)

# Configurar las sesiones y los mensajes
app.secret_key = clave_secreta
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


@app.route("/")
def inicio():
    # Consultar los datos para el panel principal
    try:
        resumen = obtener_resumen()
        vehiculos = listar_vehiculos()

        return render_template(
            "inicio.html",
            resumen=resumen,
            vehiculos=vehiculos
        )

    except Exception:
        logger.exception("Error al cargar el inicio")
        flash("No se pudo cargar la información principal.", "error")
        return render_template(
            "inicio.html",
            resumen={
                "total_vehiculos": 0,
                "vehiculos_parqueados": 0,
                "celdas_disponibles": 0,
                "celdas_ocupadas": []
            },
            vehiculos=[]
        )

@app.route("/registrar", methods=["GET"])
def formulario_registro():
    # Mostrar el formulario para registrar vehículos
    return render_template("registrar.html")


@app.route("/registrar", methods=["POST"])
def registrar():
    # Recoger y organizar los datos del formulario
    placa = request.form.get("placa", "").strip().upper()
    marca = request.form.get("marca", "").strip()
    modelo = request.form.get("modelo", "").strip()
    color = request.form.get("color", "").strip()

    # Validar que la placa tenga una longitud permitida
    if not placa or len(placa) > 10:
        flash("La placa es obligatoria y debe tener máximo 10 caracteres.", "error")
        return redirect(url_for("formulario_registro"))

    try:
        # Guardar el vehículo en la base de datos
        registrar_vehiculo(placa, marca, modelo, color)
        flash("Vehículo registrado correctamente.", "exito")

    except Exception:
        logger.exception("Error al registrar un vehículo")
        flash(
            "No se pudo registrar el vehículo. Comprueba si la placa ya existe.",
            "error"
        )

    return redirect(url_for("inicio"))

# Registrar la entrada de un vehículo
@app.route("/entrada", methods=["GET", "POST"])
def entrada():
    # Registrar la entrada cuando se envía el formulario
    if request.method == "POST":
        try:
            id_vehiculo = int(request.form.get("id_vehiculo", ""))

            resultado = registrar_entrada(id_vehiculo)

            if resultado == "registrada":
                flash("Entrada registrada correctamente.", "exito")

            elif resultado == "duplicada":
                flash(
                    "Este vehículo ya tiene una entrada registrada y sigue dentro del parqueadero.",
                    "error"
                )

            elif resultado == "sin_celdas":
                flash("No hay celdas disponibles.", "error")

        except (ValueError, TypeError):
            flash("Selecciona un vehículo válido.", "error")

        except Exception:
            logger.exception("Error al registrar una entrada")
            flash("No se pudo registrar la entrada.", "error")

        return redirect(url_for("entrada"))

    # Consultar los vehículos disponibles para registrar una entrada
    try:
        vehiculos = listar_vehiculos_para_entrada()
    except Exception:
        logger.exception("Error al consultar los vehículos")
        flash("No se pudieron consultar los vehículos.", "error")
        vehiculos = []

    return render_template("entrada.html", vehiculos=vehiculos)

@app.route("/salida", methods=["GET", "POST"])
def salida():
    # Registrar la salida cuando se envía el formulario
    if request.method == "POST":
        try:
            id_movimiento = int(request.form.get("id_movimiento", ""))

            if registrar_salida(id_movimiento):
                flash("Salida registrada correctamente. Celda liberada.", "exito")
            else:
                flash("El movimiento no existe o el vehículo ya salió.", "error")

        except (ValueError, TypeError):
            flash("Selecciona un movimiento válido.", "error")

        except Exception:
            logger.exception("Error al registrar una salida")
            flash("No se pudo registrar la salida.", "error")

        return redirect(url_for("salida"))

    # Consultar los vehículos que siguen dentro del parqueadero
    try:
        movimientos = listar_movimientos_activos()
    except Exception:
        logger.exception("Error al consultar los movimientos activos")
        flash("No se pudieron consultar los vehículos parqueados.", "error")
        movimientos = []

    return render_template("salida.html", movimientos=movimientos)


@app.route("/novedades", methods=["GET", "POST"])
def novedades():
    # Guardar la novedad cuando se envía el formulario
    if request.method == "POST":
        try:
            id_movimiento = int(request.form.get("id_movimiento", ""))
            descripcion = request.form.get("descripcion", "").strip()

            if not descripcion:
                flash("Escribe una descripción para la novedad.", "error")
            else:
                if registrar_novedad(id_movimiento, descripcion):
                    flash("Novedad registrada correctamente.", "exito")
                else:
                    flash(
                        "No se encontró una estancia activa para ese movimiento.",
                        "error"
                    )

        except (ValueError, TypeError):
            flash("Selecciona un movimiento válido.", "error")

        except Exception:
            logger.exception("Error al registrar una novedad")
            flash("No se pudo registrar la novedad.", "error")

        return redirect(url_for("novedades"))

    # Consultar los vehículos que todavía están en el parqueadero
    try:
        movimientos = listar_movimientos_activos()
    except Exception:
        logger.exception("Error al consultar las novedades")
        flash("No se pudieron consultar los vehículos parqueados.", "error")
        movimientos = []

    return render_template("novedades.html", movimientos=movimientos)


@app.route("/historial")
def historial():
    # Consultar todos los movimientos registrados
    try:
        movimientos = obtener_historial()
    except Exception:
        logger.exception("Error al consultar el historial")
        flash("No se pudo cargar el historial.", "error")
        movimientos = []

    return render_template("historial.html", movimientos=movimientos)

# Mostrar el directorio de usuarios y sus indicadores
@app.route("/usuarios")
def usuarios():
    usuarios_registrados = listar_usuarios()

    # Contar los usuarios según su estado
    total_activos = sum(1 for usuario in usuarios_registrados if usuario[6])
    total_inactivos = len(usuarios_registrados) - total_activos

    return render_template(
        "usuarios.html",
        usuarios=usuarios_registrados,
        total_activos=total_activos,
        total_inactivos=total_inactivos
    )


# Registrar un nuevo usuario
@app.route("/usuarios/registrar", methods=["GET", "POST"])
def nuevo_usuario():
    if request.method == "POST":
        documento = request.form.get("documento", "").strip()
        nombres = request.form.get("nombres", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo = request.form.get("correo", "").strip()

        # Verificar los datos obligatorios
        if not documento or not nombres or not apellidos:
            flash("Completa el documento, los nombres y los apellidos.", "error")
            return redirect(url_for("nuevo_usuario"))

        if len(documento) > 20:
            flash("El documento no puede superar los 20 caracteres.", "error")
            return redirect(url_for("nuevo_usuario"))

        try:
            # Guardar el usuario en la base de datos
            registrar_usuario(documento, nombres, apellidos, telefono, correo)
            flash("Usuario registrado correctamente.", "exito")
            return redirect(url_for("usuarios"))

        except Exception:
            logger.exception("Error al registrar un usuario")
            flash("No se pudo registrar el usuario. Comprueba si el documento ya existe.", "error")

    return render_template("usuario_formulario.html", usuario=None)


# Editar los datos de un usuario
@app.route("/usuarios/editar/<int:id_usuario>", methods=["GET", "POST"])
def editar_usuario(id_usuario):
    try:
        usuario = obtener_usuario(id_usuario)

        if usuario is None:
            flash("No se encontró el usuario.", "error")
            return redirect(url_for("usuarios"))

        if request.method == "POST":
            documento = request.form.get("documento", "").strip()
            nombres = request.form.get("nombres", "").strip()
            apellidos = request.form.get("apellidos", "").strip()
            telefono = request.form.get("telefono", "").strip()
            correo = request.form.get("correo", "").strip()

            # Validar los datos obligatorios
            if not documento or not nombres or not apellidos:
                flash("Completa los campos obligatorios.", "error")
                return redirect(url_for("editar_usuario", id_usuario=id_usuario))

            if len(documento) > 20:
                flash("El documento no puede superar los 20 caracteres.", "error")
                return redirect(url_for("editar_usuario", id_usuario=id_usuario))

            # Guardar los cambios del usuario
            actualizado = actualizar_usuario(
                id_usuario,
                documento,
                nombres,
                apellidos,
                telefono,
                correo
            )

            if actualizado:
                flash("Datos del usuario actualizados correctamente.", "exito")
            else:
                flash("No se pudieron actualizar los datos.", "error")

            return redirect(url_for("usuarios"))

        return render_template("usuario_formulario.html", usuario=usuario)

    except Exception:
        logger.exception("Error al editar un usuario")
        flash("No se pudo cargar o actualizar el usuario.", "error")
        return redirect(url_for("usuarios"))


# Activar o desactivar un usuario
@app.route("/usuarios/estado/<int:id_usuario>", methods=["POST"])
def estado_usuario(id_usuario):
    try:
        activo = request.form.get("activo") == "true"

        if cambiar_estado_usuario(id_usuario, activo):
            flash("Estado del usuario actualizado correctamente.", "exito")
        else:
            flash(
                "No se pudo cambiar el estado. Verifica si tiene vehículos dentro del parqueadero.",
                "error"
            )

    except Exception:
        logger.exception("Error al cambiar el estado del usuario")
        flash("No se pudo cambiar el estado del usuario.", "error")

    return redirect(url_for("usuarios"))


# Mostrar el directorio de celdas y sus indicadores
@app.route("/celdas")
def celdas():
    celdas_registradas = listar_celdas()

    # Contar las celdas según su estado
    total_disponibles = sum(
        1 for celda in celdas_registradas
        if not celda[2] and celda[3]
    )

    total_ocupadas = sum(
        1 for celda in celdas_registradas
        if celda[2]
    )

    total_inactivas = sum(
        1 for celda in celdas_registradas
        if not celda[3]
    )

    return render_template(
        "celdas.html",
        celdas=celdas_registradas,
        total_disponibles=total_disponibles,
        total_ocupadas=total_ocupadas,
        total_inactivas=total_inactivas
    )

# Registrar una nueva celda
@app.route("/celdas/registrar", methods=["POST"])
def nueva_celda():
    numero = request.form.get("numero", "").strip().upper()

    # Verificar que el número de celda sea válido
    if not numero or len(numero) > 10:
        flash("Ingresa un número de celda válido.", "error")
        return redirect(url_for("celdas"))

    try:
        registrada = registrar_celda(numero)

        if registrada:
            flash("Celda registrada correctamente.", "exito")
        else:
            flash("No se pueden registrar más de treinta celdas.", "error")

    except Exception:
        logger.exception("Error al registrar una celda")
        flash("No se pudo registrar la celda. Comprueba si ya existe.", "error")

    return redirect(url_for("celdas"))

# Activar o desactivar una celda
@app.route("/celdas/estado/<int:id_celda>", methods=["POST"])
def estado_celda(id_celda):
    try:
        activa = request.form.get("activa") == "true"

        if cambiar_estado_celda(id_celda, activa):
            flash("Estado de la celda actualizado correctamente.", "exito")
        else:
            flash(
                "No se puede desactivar una celda que tiene un vehículo dentro.",
                "error"
            )

    except Exception:
        logger.exception("Error al cambiar el estado de la celda")
        flash("No se pudo cambiar el estado de la celda.", "error")

    return redirect(url_for("celdas"))

# Mostrar el módulo de gestión de pagos
@app.route("/pagos")
def pagos():
    try:
        usuarios = listar_usuarios_para_pagos()
        pagos_registrados = listar_pagos()
        mensualidades = obtener_estado_mensualidades()

        return render_template(
            "pagos.html",
            usuarios=usuarios,
            pagos=pagos_registrados,
            mensualidades=mensualidades
        )

    except Exception:
        logger.exception("Error al consultar los pagos")
        flash("No se pudo cargar la información de pagos.", "error")

        return render_template(
            "pagos.html",
            usuarios=[],
            pagos=[],
            mensualidades=[]
        )

# Registrar una nueva mensualidad
@app.route("/pagos/registrar", methods=["POST"])
def nuevo_pago():
    try:
        id_usuario = int(request.form.get("id_usuario", ""))
        mes = int(request.form.get("mes", ""))
        anio = int(request.form.get("anio", ""))
        metodo_pago = request.form.get("metodo_pago", "")

        # Validar los datos del pago
        if id_usuario <= 0 or mes < 1 or mes > 12:
            flash("Selecciona un usuario y un período válidos.", "error")
            return redirect(url_for("pagos"))

        if anio < 2000 or anio > 2100:
            flash("Ingresa un año válido.", "error")
            return redirect(url_for("pagos"))

        if metodo_pago not in ["Efectivo", "Transferencia", "Tarjeta"]:
            flash("Selecciona un método de pago válido.", "error")
            return redirect(url_for("pagos"))

        # Validar si el pago está permitido
        permitido, mensaje = validar_pago(
            id_usuario,
            mes,
            anio
        )

        if not permitido:
            flash(mensaje, "error")
            return redirect(url_for("pagos"))

        # Guardar el pago
        registrado = registrar_pago(
            id_usuario,
            mes,
            anio,
            metodo_pago
        )

        if registrado:
            flash("Pago registrado correctamente.", "exito")
        else:
            flash("Este usuario ya tiene un pago para ese período.", "error")

    except (ValueError, TypeError):
        flash("Verifica los datos ingresados.", "error")

    except Exception:
        logger.exception("Error al registrar un pago")
        flash("No se pudo registrar el pago.", "error")

    return redirect(url_for("pagos"))

# Consultar el historial de pagos de un usuario
@app.route("/pagos/historial/<int:id_usuario>")
def historial_pagos(id_usuario):
    try:
        usuario = obtener_usuario(id_usuario)

        if usuario is None:
            flash("No se encontró el usuario.", "error")
            return redirect(url_for("pagos"))

        historial = obtener_historial_pagos(id_usuario)

        return render_template(
            "historial_pagos.html",
            usuario=usuario,
            historial=historial
        )

    except Exception:
        logger.exception("Error al consultar el historial de pagos")
        flash("No se pudo consultar el historial.", "error")
        return redirect(url_for("pagos"))

# Eliminar una celda del parqueadero
@app.route("/celdas/eliminar/<int:id_celda>", methods=["POST"])
def eliminar_celda_ruta(id_celda):
    try:
        resultado = eliminar_celda(id_celda)

        if resultado == "eliminada":
            flash("Celda eliminada correctamente.", "exito")

        elif resultado == "ocupada":
            flash("No se puede eliminar una celda ocupada.", "error")

        elif resultado == "orden":
            flash("Solo se puede eliminar la última celda registrada.", "error")

        elif resultado == "historial":
            flash("No se puede eliminar una celda que tenga movimientos registrados.", "error")

        elif resultado == "minimo":
            flash("El parqueadero debe conservar como mínimo diez celdas.", "error")

        else:
            flash("La celda no existe.", "error")

    except Exception:
        logger.exception("Error al eliminar una celda")
        flash("No se pudo eliminar la celda.", "error")

    return redirect("/celdas")

# Iniciar el servidor cuando se ejecuta este archivo
if __name__ == "__main__":
    modo_pruebas = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=modo_pruebas)
