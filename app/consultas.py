# Importar la conexión con la base de datos
from conexion import obtener_conexion


def obtener_resumen():
    # Consultar los datos generales del parqueadero
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM vehiculos")
    total_vehiculos = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM movimientos
        WHERE fecha_salida IS NULL
    """)
    vehiculos_parqueados = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM celdas
        WHERE ocupada = FALSE AND activa = TRUE
    """)
    celdas_disponibles = cursor.fetchone()[0]

    cursor.execute("""
        SELECT numero
        FROM celdas
        WHERE ocupada = TRUE
        ORDER BY numero
    """)
    celdas_ocupadas = cursor.fetchall()

    cursor.close()
    conexion.close()

    # Organizar los datos para mostrarlos en el inicio
    return {
        "total_vehiculos": total_vehiculos,
        "vehiculos_parqueados": vehiculos_parqueados,
        "celdas_disponibles": celdas_disponibles,
        "celdas_ocupadas": [celda[0] for celda in celdas_ocupadas]
    }


def listar_vehiculos():
    # Consultar los vehículos registrados
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT placa, marca, modelo, color
        FROM vehiculos
        ORDER BY id_vehiculo DESC
    """)

    vehiculos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return vehiculos


def registrar_vehiculo(placa, marca, modelo, color):
    # Guardar el nuevo vehículo
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO vehiculos (placa, marca, modelo, color)
            VALUES (%s, %s, %s, %s)
        """, (placa, marca or None, modelo or None, color or None))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def listar_vehiculos_para_entrada():
    # Consultar los vehículos que pueden ingresar
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id_vehiculo, placa
        FROM vehiculos
        ORDER BY placa
    """)

    vehiculos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return vehiculos


def registrar_entrada(id_vehiculo):
    # Buscar y bloquear una celda libre y activa
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT id_celda
            FROM celdas
            WHERE ocupada = FALSE
              AND activa = TRUE
            ORDER BY numero
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)

        celda = cursor.fetchone()

        if celda is None:
            conexion.rollback()
            return False

        id_celda = celda[0]

        # Registrar la entrada del vehículo
        cursor.execute("""
            INSERT INTO movimientos (id_vehiculo, id_celda)
            VALUES (%s, %s)
        """, (id_vehiculo, id_celda))

        # Marcar la celda como ocupada
        cursor.execute("""
            UPDATE celdas
            SET ocupada = TRUE
            WHERE id_celda = %s
        """, (id_celda,))

        conexion.commit()
        return True

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def listar_movimientos_activos():
    # Consultar los vehículos que siguen dentro del parqueadero
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            m.id_movimiento,
            v.placa,
            c.numero,
            m.fecha_entrada
        FROM movimientos AS m
        JOIN vehiculos AS v
            ON m.id_vehiculo = v.id_vehiculo
        JOIN celdas AS c
            ON m.id_celda = c.id_celda
        WHERE m.fecha_salida IS NULL
        ORDER BY m.fecha_entrada
    """)

    movimientos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return movimientos


def registrar_salida(id_movimiento):
    # Buscar y bloquear el movimiento que se va a cerrar
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT id_celda
            FROM movimientos
            WHERE id_movimiento = %s
              AND fecha_salida IS NULL
            FOR UPDATE
        """, (id_movimiento,))

        movimiento = cursor.fetchone()

        if movimiento is None:
            conexion.rollback()
            return False

        id_celda = movimiento[0]

        # Registrar la hora de salida
        cursor.execute("""
            UPDATE movimientos
            SET fecha_salida = CURRENT_TIMESTAMP
            WHERE id_movimiento = %s
              AND fecha_salida IS NULL
        """, (id_movimiento,))

        # Liberar la celda utilizada
        cursor.execute("""
            UPDATE celdas
            SET ocupada = FALSE
            WHERE id_celda = %s
        """, (id_celda,))

        conexion.commit()
        return True

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def registrar_novedad(id_movimiento, descripcion):
    # Registrar una novedad asociada a una estancia activa
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO novedades (id_movimiento, descripcion)
            SELECT id_movimiento, %s
            FROM movimientos
            WHERE id_movimiento = %s
              AND fecha_salida IS NULL
            RETURNING id_novedad
        """, (descripcion, id_movimiento))

        novedad = cursor.fetchone()

        if novedad is None:
            conexion.rollback()
            return False

        conexion.commit()
        return True

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


def obtener_historial():
    # Consultar las entradas, salidas y novedades registradas
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            m.id_movimiento,
            v.placa,
            c.numero,
            m.fecha_entrada,
            m.fecha_salida,
            COALESCE(
                STRING_AGG(n.descripcion, ' | ' ORDER BY n.fecha_novedad),
                '-'
            )
        FROM movimientos m
        JOIN vehiculos v
            ON v.id_vehiculo = m.id_vehiculo
        JOIN celdas c
            ON c.id_celda = m.id_celda
        LEFT JOIN novedades n
            ON n.id_movimiento = m.id_movimiento
        GROUP BY
            m.id_movimiento,
            v.placa,
            c.numero,
            m.fecha_entrada,
            m.fecha_salida
        ORDER BY m.fecha_entrada DESC
    """)

    movimientos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return movimientos


# Consultar todos los usuarios registrados
def listar_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT
                id_usuario,
                documento,
                nombres,
                apellidos,
                telefono,
                correo,
                activo
            FROM usuarios
            ORDER BY id_usuario DESC
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()


# Registrar un nuevo usuario
def registrar_usuario(documento, nombres, apellidos, telefono, correo):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (
                documento, nombres, apellidos, telefono, correo
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            documento,
            nombres,
            apellidos,
            telefono or None,
            correo or None
        ))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


# Actualizar los datos de un usuario
def actualizar_usuario(id_usuario, documento, nombres, apellidos, telefono, correo):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            UPDATE usuarios
            SET documento = %s,
                nombres = %s,
                apellidos = %s,
                telefono = %s,
                correo = %s
            WHERE id_usuario = %s
        """, (
            documento,
            nombres,
            apellidos,
            telefono or None,
            correo or None,
            id_usuario
        ))

        actualizado = cursor.rowcount > 0
        conexion.commit()
        return actualizado

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


# Activar o desactivar un usuario
def cambiar_estado_usuario(id_usuario, activo):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        # Evitar desactivar usuarios con vehículos dentro del parqueadero
        if not activo:
            cursor.execute("""
                SELECT COUNT(*)
                FROM vehiculos v
                JOIN movimientos m
                    ON m.id_vehiculo = v.id_vehiculo
                WHERE v.id_usuario = %s
                  AND m.fecha_salida IS NULL
            """, (id_usuario,))

            if cursor.fetchone()[0] > 0:
                conexion.rollback()
                return False

        cursor.execute("""
            UPDATE usuarios
            SET activo = %s
            WHERE id_usuario = %s
        """, (activo, id_usuario))

        actualizado = cursor.rowcount > 0
        conexion.commit()
        return actualizado

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


# Consultar todas las celdas del parqueadero
def listar_celdas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT
                id_celda,
                numero,
                ocupada,
                activa
            FROM celdas
            ORDER BY numero
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()


# Registrar una nueva celda
def registrar_celda(numero):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO celdas (numero, ocupada, activa)
            VALUES (%s, FALSE, TRUE)
        """, (numero,))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()


# Consultar el estado de una celda
def consultar_estado_celda(id_celda):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT numero, ocupada, activa
            FROM celdas
            WHERE id_celda = %s
        """, (id_celda,))

        return cursor.fetchone()

    finally:
        cursor.close()
        conexion.close()


# Activar o desactivar una celda
def cambiar_estado_celda(id_celda, activa):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        # Consultar la celda y bloquearla mientras se actualiza
        cursor.execute("""
            SELECT ocupada
            FROM celdas
            WHERE id_celda = %s
            FOR UPDATE
        """, (id_celda,))

        celda = cursor.fetchone()

        if celda is None:
            conexion.rollback()
            return False

        # Evitar desactivar una celda que tiene un vehículo
        if not activa and celda[0]:
            conexion.rollback()
            return False

        # Actualizar el estado de actividad
        cursor.execute("""
            UPDATE celdas
            SET activa = %s
            WHERE id_celda = %s
        """, (activa, id_celda))

        conexion.commit()
        return True

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()

# Consultar los datos de un usuario específico
def obtener_usuario(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT
                id_usuario,
                documento,
                nombres,
                apellidos,
                telefono,
                correo,
                activo
            FROM usuarios
            WHERE id_usuario = %s
        """, (id_usuario,))

        return cursor.fetchone()

    finally:
        cursor.close()
        conexion.close()
