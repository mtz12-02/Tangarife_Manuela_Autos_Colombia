-- =============================================
-- AUTOS COLOMBIA
-- Script de creación de la base de datos
-- Ingeniería de Software
-- =============================================

BEGIN;

-- =============================================
-- 1. TABLA DE USUARIOS
-- =============================================

CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    documento VARCHAR(20) NOT NULL UNIQUE,
    nombres VARCHAR(80) NOT NULL,
    apellidos VARCHAR(80) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(100),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 2. TABLA DE VEHICULOS
-- =============================================

CREATE TABLE vehiculos (
    id_vehiculo SERIAL PRIMARY KEY,
    placa VARCHAR(10) NOT NULL UNIQUE,
    marca VARCHAR(50),
    modelo VARCHAR(50),
    color VARCHAR(30),
    id_usuario INTEGER REFERENCES usuarios(id_usuario)
);

-- =============================================
-- 3. TABLA DE CELDAS
-- =============================================

CREATE TABLE celdas (
    id_celda SERIAL PRIMARY KEY,
    numero VARCHAR(10) NOT NULL UNIQUE,
    ocupada BOOLEAN NOT NULL DEFAULT FALSE,
    activa BOOLEAN NOT NULL DEFAULT TRUE
);

-- =============================================
-- 4. TABLA DE MOVIMIENTOS
-- =============================================

CREATE TABLE movimientos (
    id_movimiento SERIAL PRIMARY KEY,
    id_vehiculo INTEGER NOT NULL
        REFERENCES vehiculos(id_vehiculo),
    id_celda INTEGER NOT NULL
        REFERENCES celdas(id_celda),
    fecha_entrada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_salida TIMESTAMP,

    CONSTRAINT salida_posterior_entrada
        CHECK (
            fecha_salida IS NULL
            OR fecha_salida >= fecha_entrada
        )
);

-- Evitar dos entradas abiertas para un vehículo
CREATE UNIQUE INDEX una_entrada_abierta_por_vehiculo
ON movimientos (id_vehiculo)
WHERE fecha_salida IS NULL;

-- Evitar asignar una celda a dos vehículos simultáneamente
CREATE UNIQUE INDEX una_ocupacion_por_celda
ON movimientos (id_celda)
WHERE fecha_salida IS NULL;

-- =============================================
-- 5. TABLA DE NOVEDADES
-- =============================================

CREATE TABLE novedades (
    id_novedad SERIAL PRIMARY KEY,
    id_movimiento INTEGER NOT NULL
        REFERENCES movimientos(id_movimiento),
    fecha_novedad TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    descripcion TEXT NOT NULL
);

-- =============================================
-- 6. TABLA DE PAGOS
-- =============================================

CREATE TABLE pagos (
    id_pago INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario INTEGER NOT NULL,
    mes SMALLINT NOT NULL,
    anio SMALLINT NOT NULL,
    valor NUMERIC(10,2) NOT NULL DEFAULT 150000,
    metodo_pago VARCHAR(20) NOT NULL,
    fecha_pago TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pagos_mes_check
        CHECK (mes BETWEEN 1 AND 12),

    CONSTRAINT pagos_valor_check
        CHECK (valor = 150000),

    CONSTRAINT pagos_metodo_pago_check
        CHECK (
            metodo_pago IN (
                'Efectivo',
                'Transferencia',
                'Tarjeta'
            )
        ),

    CONSTRAINT fk_pagos_usuarios
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios(id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT uq_pago_usuario_periodo
        UNIQUE (id_usuario, mes, anio)
);

-- =============================================
-- 7. DATOS INICIALES DE CELDAS
-- =============================================

INSERT INTO celdas (numero)
VALUES
    ('C01'),
    ('C02'),
    ('C03'),
    ('C04'),
    ('C05'),
    ('C06'),
    ('C07'),
    ('C08'),
    ('C09'),
    ('C10')
ON CONFLICT (numero) DO NOTHING;

COMMIT;

-- =============================================
-- FIN DEL SCRIPT
-- =============================================
