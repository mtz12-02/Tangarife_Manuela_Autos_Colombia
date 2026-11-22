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
        WHERE ocupada = FALSE
        AND activa = TRUE
        AND eliminada = FALSE
    """)
    celdas_disponibles = cursor.fetchone()[0]

    cursor.execute("""
        SELECT numero
        FROM celdas
        WHERE ocupada = TRUE
        AND eliminada = FALSE
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
        SELECT v.id_vehiculo, v.placa
        FROM vehiculos v
        WHERE NOT EXISTS (
            SELECT 1
            FROM movimientos m
            WHERE m.id_vehiculo = v.id_vehiculo
              AND m.fecha_salida IS NULL
        )
        ORDER BY v.placa
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
        # Comprobar que el vehículo no esté parqueado
        cursor.execute("""
            SELECT id_movimiento
            FROM movimientos
            WHERE id_vehiculo = %s
              AND fecha_salida IS NULL
            FOR UPDATE
        """, (id_vehiculo,))

        movimiento = cursor.fetchone()

        if movimiento is not None:
            conexion.rollback()
            return "duplicada"

        # Buscar una celda libre y activa
        cursor.execute("""
            SELECT id_celda
            FROM celdas
            WHERE ocupada = FALSE
              AND activa = TRUE
              AND eliminada = FALSE
            ORDER BY numero
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """)

        celda = cursor.fetchone()

        if celda is None:
            conexion.rollback()
            return "sin_celdas"

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
              AND eliminada = FALSE
        """, (id_celda,))

        conexion.commit()
        return "registrada"

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

# Consultar todas las celdas activas del parqueadero
def listar_celdas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT
                c.id_celda,
                c.numero,
                c.ocupada,
                c.activa,
                (
                    c.id_celda = (
                        SELECT MAX(id_celda)
                        FROM celdas
                        WHERE eliminada = FALSE
                    )
                    AND c.ocupada = FALSE
                    AND (
                        SELECT COUNT(*)
                        FROM celdas
                        WHERE eliminada = FALSE
                    ) > 10
                ) AS puede_eliminar
            FROM celdas c
            WHERE c.eliminada = FALSE
            ORDER BY c.id_celda
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
        # Bloquear la tabla mientras se registra o recupera una celda
        cursor.execute("LOCK TABLE celdas IN EXCLUSIVE MODE")

        # Comprobar si el número ya existe
        cursor.execute("""
            SELECT id_celda, eliminada
            FROM celdas
            WHERE numero = %s
        """, (numero,))

        celda = cursor.fetchone()

        # Consultar cuántas celdas siguen registradas
        cursor.execute("""
            SELECT COUNT(*)
            FROM celdas
            WHERE eliminada = FALSE
        """)
        total_celdas = cursor.fetchone()[0]

        if total_celdas >= 30:
            conexion.rollback()
            return False

        # Recuperar la celda si anteriormente fue eliminada
        if celda is not None:
            if celda[1]:
                cursor.execute("""
                    UPDATE celdas
                    SET eliminada = FALSE,
                        ocupada = FALSE,
                        activa = TRUE
                    WHERE id_celda = %s
                """, (celda[0],))

                conexion.commit()
                return True

            conexion.rollback()
            return False

        # Registrar una celda nueva
        cursor.execute("""
            INSERT INTO celdas (numero, ocupada, activa)
            VALUES (%s, FALSE, TRUE)
        """, (numero,))

        conexion.commit()
        return True

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
            AND eliminada = FALSE
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
            AND eliminada = FALSE
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
# Consultar los usuarios para registrar sus mensualidades
def listar_usuarios_para_pagos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT
                id_usuario,
                documento,
                nombres,
                apellidos
            FROM usuarios
            WHERE activo = TRUE
            ORDER BY nombres, apellidos 
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()

# Registrar el pago de una mensualidad
def registrar_pago(id_usuario, mes, anio, metodo_pago):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO pagos (
                id_usuario,
                mes,
                anio,
                metodo_pago
            )
            VALUES (%s, %s, %s, %s)
        """, (id_usuario, mes, anio, metodo_pago))

        conexion.commit()
        return True

    except Exception as error:
        conexion.rollback()

        # Evitar pagos duplicados para el mismo período
        if getattr(error, "sqlstate", None) == "23505":
            return False

        raise

    finally:
        cursor.close()
        conexion.close()

# Consultar el historial de pagos de un usuario
def obtener_historial_pagos(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT
                mes,
                anio,
                valor,
                metodo_pago,
                fecha_pago
            FROM pagos
            WHERE id_usuario = %s
            ORDER BY anio DESC, mes DESC
        """, (id_usuario,))

        return cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()

# Consultar todos los pagos registrados
def listar_pagos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT
                u.documento,
                u.nombres,
                u.apellidos,
                p.mes,
                p.anio,
                p.valor,
                p.metodo_pago,
                p.fecha_pago
            FROM pagos AS p
            JOIN usuarios AS u
                ON p.id_usuario = u.id_usuario
            ORDER BY p.fecha_pago DESC
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()

# Consultar el estado de las mensualidades de los usuarios
def obtener_estado_mensualidades():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT
                u.id_usuario,
                u.documento,
                u.nombres,
                u.apellidos,
                EXTRACT(MONTH FROM periodos.periodo)::INTEGER AS mes,
                EXTRACT(YEAR FROM periodos.periodo)::INTEGER AS anio,
                CASE
                    WHEN p.id_pago IS NULL THEN 'Pendiente'
                    ELSE 'Pagado'
                END AS estado,
                p.valor,
                p.metodo_pago,
                p.fecha_pago
            FROM usuarios AS u

            CROSS JOIN LATERAL generate_series(
                date_trunc('month', u.fecha_registro),
                date_trunc('month', CURRENT_DATE::timestamp)
                    + INTERVAL '5 months',
                INTERVAL '1 month'
            ) AS periodos(periodo)

            LEFT JOIN pagos AS p
                ON p.id_usuario = u.id_usuario
                AND p.mes = EXTRACT(MONTH FROM periodos.periodo)
                AND p.anio = EXTRACT(YEAR FROM periodos.periodo)

            WHERE u.activo = TRUE
              AND (
                  periodos.periodo <= date_trunc(
                      'month', CURRENT_DATE::timestamp
                  )
                  OR p.id_pago IS NOT NULL
              )

            ORDER BY
                u.apellidos,
                u.nombres,
                periodos.periodo DESC
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()

# Validar las condiciones para registrar un pago
def validar_pago(id_usuario, mes, anio):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT fecha_registro::date, activo, CURRENT_DATE
            FROM usuarios
            WHERE id_usuario = %s
        """, (id_usuario,))

        usuario = cursor.fetchone()

        if not usuario or not usuario[1]:
            return False, "El usuario no está activo."

        fecha_inicio = usuario[0]
        fecha_actual = usuario[2]

        # Comparar los períodos mensuales
        periodo_inicio = fecha_inicio.year * 12 + fecha_inicio.month
        periodo_actual = fecha_actual.year * 12 + fecha_actual.month
        periodo_pago = anio * 12 + mes

        if periodo_pago < periodo_inicio:
            return False, "No se puede pagar un período anterior al registro del usuario."

        # Limitar los pagos anticipados a cinco meses
        if periodo_pago > periodo_actual + 5:
            return False, "Solo se permite anticipar hasta cinco meses."

        # Verificar si el usuario está al día para pagar anticipadamente
        if periodo_pago > periodo_actual:

            cursor.execute("""
                SELECT COUNT(*)
                FROM generate_series(
                    date_trunc('month', %s::date),
                    date_trunc('month', CURRENT_DATE),
                    interval '1 month'
                ) AS periodos(periodo)

                LEFT JOIN pagos AS p
                    ON p.id_usuario = %s
                    AND p.mes = EXTRACT(MONTH FROM periodos.periodo)
                    AND p.anio = EXTRACT(YEAR FROM periodos.periodo)

                WHERE p.id_pago IS NULL
            """, (fecha_inicio, id_usuario))

            pendientes = cursor.fetchone()[0]

            if pendientes > 0:
                return False, "El usuario debe estar al día para realizar pagos anticipados."

        return True, "Pago permitido."

    finally:
        cursor.close()
        conexion.close()

# Eliminar una celda sin perder su historial
def eliminar_celda(id_celda):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        # Bloquear las celdas mientras se realiza la operación
        cursor.execute("LOCK TABLE celdas IN EXCLUSIVE MODE")

        # Consultar si la celda existe y está ocupada
        cursor.execute("""
            SELECT ocupada
            FROM celdas
            WHERE id_celda = %s
            AND eliminada = FALSE
            FOR UPDATE
        """, (id_celda,))

        celda = cursor.fetchone()

        if celda is None:
            return "no_existe"

        if celda[0]:
            return "ocupada"

        # Consultar cuántas celdas existen
        cursor.execute("""
            SELECT COUNT(*)
            FROM celdas
            WHERE eliminada = FALSE
        """)

        total_celdas = cursor.fetchone()[0]

        if total_celdas <= 10:
            return "minimo"

        # Consultar la última celda registrada
        cursor.execute("""
            SELECT MAX(id_celda)
            FROM celdas
            WHERE eliminada = FALSE
        """)

        ultima_celda = cursor.fetchone()[0]

        if id_celda != ultima_celda:
            return "orden"

        # Marcar la celda como eliminada
        cursor.execute("""
            UPDATE celdas
            SET eliminada = TRUE
            WHERE id_celda = %s
        """, (id_celda,))

        conexion.commit()
        return "eliminada"

    except Exception:
        conexion.rollback()
        raise

    finally:
        cursor.close()
        conexion.close()