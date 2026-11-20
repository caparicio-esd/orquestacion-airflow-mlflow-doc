-- ============================================================================
-- init_carrefour_db.sql
-- Crea la base de datos analítica `carrefour_dw` y la arquitectura Medallion
-- (esquemas bronze, silver, gold) para los ejercicios de clase.
-- ============================================================================

CREATE DATABASE carrefour_dw;

\connect carrefour_dw

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- Catálogo maestro de tiendas Carrefour (referencia para enriquecimiento)
CREATE TABLE IF NOT EXISTS silver.dim_tiendas (
    tienda_id       VARCHAR(16) PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL,
    formato         VARCHAR(32)  NOT NULL,  -- Hipermercado, Market, Express
    provincia       VARCHAR(64)  NOT NULL
);

INSERT INTO silver.dim_tiendas (tienda_id, nombre, formato, provincia) VALUES
    ('CRF-MAD-01', 'Carrefour Hortaleza',    'Hipermercado', 'Madrid'),
    ('CRF-MAD-02', 'Carrefour Alcobendas',   'Hipermercado', 'Madrid'),
    ('CRF-MAD-03', 'Carrefour Express Sol',  'Express',      'Madrid'),
    ('CRF-BCN-01', 'Carrefour Glories',      'Hipermercado', 'Barcelona'),
    ('CRF-VLC-01', 'Carrefour Campanar',     'Market',       'Valencia')
ON CONFLICT (tienda_id) DO NOTHING;

-- Capa BRONZE: ingesta cruda (append-only por fecha_batch, sin restricciones fuertes)
CREATE TABLE IF NOT EXISTS bronze.tickets_raw (
    id_ingesta      SERIAL PRIMARY KEY,
    fecha_batch     DATE        NOT NULL,
    ticket_id       VARCHAR(32),
    tienda_id       VARCHAR(32),
    cliente_club    VARCHAR(16),
    categoria       VARCHAR(64),
    importe_eur     NUMERIC(10, 2),
    unidades        INTEGER,
    ingestado_en    TIMESTAMP DEFAULT NOW()
);

-- Capa SILVER: tickets limpios, deduplicados y tipados (idempotente por ticket_id)
CREATE TABLE IF NOT EXISTS silver.tickets_clean (
    ticket_id       VARCHAR(32) PRIMARY KEY,
    fecha_batch     DATE          NOT NULL,
    tienda_id       VARCHAR(16)   NOT NULL REFERENCES silver.dim_tiendas(tienda_id),
    es_socio_club   BOOLEAN       NOT NULL,
    categoria       VARCHAR(64)   NOT NULL,
    importe_eur     NUMERIC(10,2) NOT NULL CHECK (importe_eur > 0),
    unidades        INTEGER       NOT NULL CHECK (unidades > 0),
    procesado_en    TIMESTAMP DEFAULT NOW()
);

-- Capa SILVER (cuarentena): registros descartados para auditoría de calidad
CREATE TABLE IF NOT EXISTS silver.tickets_quarantine (
    id_error        SERIAL PRIMARY KEY,
    fecha_batch     DATE        NOT NULL,
    ticket_id       VARCHAR(32),
    tienda_id       VARCHAR(32),
    importe_eur     NUMERIC(10, 2),
    motivo_rechazo  VARCHAR(128) NOT NULL,
    registrado_en   TIMESTAMP DEFAULT NOW()
);

-- Capa GOLD: agregados diarios de negocio listos para BI y ML
CREATE TABLE IF NOT EXISTS gold.ventas_diarias_tienda (
    fecha_batch          DATE          NOT NULL,
    tienda_id            VARCHAR(16)   NOT NULL,
    nombre_tienda        VARCHAR(120)  NOT NULL,
    formato              VARCHAR(32)   NOT NULL,
    num_tickets          INTEGER       NOT NULL,
    facturacion_eur      NUMERIC(12,2) NOT NULL,
    ticket_medio_eur     NUMERIC(10,2) NOT NULL,
    pct_socios_club      NUMERIC(5,2)  NOT NULL,
    actualizado_en       TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (fecha_batch, tienda_id)
);

-- Tabla de alertas operativas consumida por el DAG reactivo (Asset de Airflow 3)
CREATE TABLE IF NOT EXISTS gold.alertas_operativas (
    id_alerta       SERIAL PRIMARY KEY,
    fecha_batch     DATE         NOT NULL,
    tienda_id       VARCHAR(16)  NOT NULL,
    severidad       VARCHAR(16)  NOT NULL,
    mensaje         TEXT         NOT NULL,
    creado_en       TIMESTAMP DEFAULT NOW()
);
