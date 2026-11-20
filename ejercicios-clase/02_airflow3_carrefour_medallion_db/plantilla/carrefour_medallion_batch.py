"""
PLANTILLA PARA CLASE — DAG 1: Refinado por batches Medallion (Carrefour)
Completa los bloques marcados con `# TODO` usando Apache Airflow 3 (`airflow.sdk`).
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from airflow.sdk import Asset, dag, task

# TODO 1: Define el Asset de Airflow 3 para `postgres://carrefour_dw/gold/ventas_diarias_tienda`
ASSET_GOLD_VENTAS = Asset("postgres://carrefour_dw/gold/ventas_diarias_tienda")

TIENDAS_VALIDAS = ["CRF-MAD-01", "CRF-MAD-02", "CRF-MAD-03", "CRF-BCN-01", "CRF-VLC-01"]
CATEGORIAS_SUCIAS = ["  frescos ", "ALIMENTACION", "Bebidas", "electronica", "Hogar", None]


def generar_lote_tickets_sucio(fecha_ds: str, n_tickets: int = 80) -> list[tuple[Any, ...]]:
    rng = random.Random(f"carrefour-{fecha_ds}")
    filas = []
    for i in range(1, n_tickets + 1):
        ticket_id = f"TKT-{fecha_ds.replace('-', '')}-{i:04d}"
        tienda = rng.choice(TIENDAS_VALIDAS)
        socio = rng.choice(["SI", "si", "NO", "no", "1", "0"])
        categoria = rng.choice(CATEGORIAS_SUCIAS)
        importe = round(rng.uniform(4.5, 95.0), 2)
        unidades = rng.randint(1, 12)
        if i % 17 == 0:
            importe = -15.0
        elif i % 23 == 0:
            tienda = "CRF-XXX-99"
        filas.append((fecha_ds, ticket_id, tienda, socio, categoria, importe, unidades))
        if i in (5, 12):
            filas.append((fecha_ds, ticket_id, tienda, socio, categoria, importe, unidades))
    return filas


# TODO 2: Añade el decorador @dag (dag_id="carrefour_medallion_batch", schedule="@daily", catchup=False)
@dag(
    dag_id="carrefour_medallion_batch",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={"owner": "clase", "retries": 1, "retry_delay": timedelta(seconds=15)},
    tags=["clase", "airflow3", "carrefour"],
)
def carrefour_medallion_batch():
    @task
    def ingestar_batch_bronze(ds: str = "") -> dict[str, Any]:
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        hook = PostgresHook(postgres_conn_id="carrefour_pg")
        lote = generar_lote_tickets_sucio(ds)

        # TODO 3: Inserta `lote` en `bronze.tickets_raw` de forma idempotente para `fecha_batch = ds`
        # Pista: primero DELETE FROM bronze.tickets_raw WHERE fecha_batch = %s, luego executemany INSERT
        raise NotImplementedError("Completa la ingesta Bronze en clase")

    @task
    def refinar_bronze_a_silver(meta_bronze: dict[str, Any]) -> dict[str, Any]:
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        ds = meta_bronze["fecha_batch"]
        hook = PostgresHook(postgres_conn_id="carrefour_pg")

        # TODO 4: Lee `bronze.tickets_raw` de `ds`, deduplica por `ticket_id`, valida tienda/importe/unidades,
        # normaliza `es_socio_club` y `categoria`, guarda válidos en `silver.tickets_clean`
        # y descartados en `silver.tickets_quarantine` (borrando previamente la partición `ds`).
        raise NotImplementedError("Completa el refinado a Silver en clase")

    # TODO 5: Añade `outlets=[ASSET_GOLD_VENTAS]` al decorador @task
    @task
    def agregar_silver_a_gold(meta_silver: dict[str, Any]) -> dict[str, Any]:
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        ds = meta_silver["fecha_batch"]
        hook = PostgresHook(postgres_conn_id="carrefour_pg")

        # TODO 6: Calcula `gold.ventas_diarias_tienda` con JOIN a `silver.dim_tiendas`
        # (num_tickets, facturacion_eur, ticket_medio_eur, pct_socios_club) de forma idempotente.
        raise NotImplementedError("Completa la agregación Gold en clase")

    # TODO 7: Encadena las tres tareas pasando solo los diccionarios de metadatos
    meta_b = ingestar_batch_bronze()
    meta_s = refinar_bronze_a_silver(meta_b)
    agregar_silver_a_gold(meta_s)


carrefour_medallion_batch()
