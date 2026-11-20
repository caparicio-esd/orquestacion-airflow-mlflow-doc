"""
SOLUCIÓN — DAG 1: Refinado por batches Medallion (Bronze -> Silver -> Gold)
Caso de uso: Tickets de cajas TPV de tiendas Carrefour en PostgreSQL.
Sintaxis: Apache Airflow 3 (Task SDK: `from airflow.sdk import dag, task, Asset`).
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from airflow.sdk import Asset, dag, task

# Asset de Airflow 3: representa la tabla Gold actualizada al final del batch
ASSET_GOLD_VENTAS = Asset("postgres://carrefour_dw/gold/ventas_diarias_tienda")

TIENDAS_VALIDAS = ["CRF-MAD-01", "CRF-MAD-02", "CRF-MAD-03", "CRF-BCN-01", "CRF-VLC-01"]
CATEGORIAS_SUCIAS = ["  frescos ", "ALIMENTACION", "Bebidas", "electronica", "Hogar", None]


def generar_lote_tickets_sucio(fecha_ds: str, n_tickets: int = 80) -> list[tuple[Any, ...]]:
    """Genera un batch determinista para `fecha_ds` con anomalías realistas de TPV."""
    rng = random.Random(f"carrefour-{fecha_ds}")
    filas: list[tuple[Any, ...]] = []

    for i in range(1, n_tickets + 1):
        ticket_id = f"TKT-{fecha_ds.replace('-', '')}-{i:04d}"
        tienda = rng.choice(TIENDAS_VALIDAS)
        socio = rng.choice(["SI", "si", "NO", "no", "1", "0"])
        categoria = rng.choice(CATEGORIAS_SUCIAS)
        # Express Sol tiene tickets algo más pequeños para provocar alertas realistas
        base = 22.0 if tienda == "CRF-MAD-03" else 58.0
        importe = round(rng.uniform(4.5, base * 1.9), 2)
        unidades = rng.randint(1, 14)

        # Inyectamos errores realistas en ~12% de los tickets
        if i % 17 == 0:
            importe = -round(rng.uniform(5.0, 40.0), 2)  # Error: importe negativo
        elif i % 23 == 0:
            tienda = "CRF-XXX-99"  # Error: tienda inexistente en catálogo
        elif i % 29 == 0:
            unidades = 0  # Error: 0 unidades

        filas.append((fecha_ds, ticket_id, tienda, socio, categoria, importe, unidades))

        # Simulamos duplicados por reintento de red del TPV
        if i in (5, 12, 31):
            filas.append((fecha_ds, ticket_id, tienda, socio, categoria, importe, unidades))

    return filas


@dag(
    dag_id="carrefour_medallion_batch",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={
        "owner": "equipo-datos-carrefour",
        "retries": 2,
        "retry_delay": timedelta(seconds=20),
    },
    tags=["clase", "airflow3", "carrefour", "medallion", "postgres"],
    doc_md="Pipeline Medallion idempotente por batches (Bronze -> Silver -> Gold) en PostgreSQL.",
)
def carrefour_medallion_batch():
    @task
    def ingestar_batch_bronze(ds: str = "") -> dict[str, Any]:
        """Paso 1 (Bronze): ingesta el lote crudo del día en `bronze.tickets_raw`."""
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        hook = PostgresHook(postgres_conn_id="carrefour_pg")
        lote = generar_lote_tickets_sucio(ds, n_tickets=80)

        # Limpieza idempotente de la partición del día en Bronze antes de cargar
        with hook.get_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM bronze.tickets_raw WHERE fecha_batch = %s;", (ds,))
            cur.executemany(
                """
                INSERT INTO bronze.tickets_raw
                    (fecha_batch, ticket_id, tienda_id, cliente_club, categoria, importe_eur, unidades)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                lote,
            )
            conn.commit()

        print(f"[BRONZE] Fecha={ds} | Filas crudas ingestadas={len(lote)}")
        # Regla de oro: por XCom pasamos SOLO metadatos ligeros, nunca los datos
        return {"fecha_batch": ds, "filas_bronze": len(lote)}

    @task
    def refinar_bronze_a_silver(meta_bronze: dict[str, Any]) -> dict[str, Any]:
        """Paso 2 (Silver): deduplica, normaliza, valida calidad y separa cuarentena."""
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        ds = meta_bronze["fecha_batch"]
        hook = PostgresHook(postgres_conn_id="carrefour_pg")

        with hook.get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT tienda_id FROM silver.dim_tiendas;")
            tiendas_ok = {row[0] for row in cur.fetchall()}

            cur.execute(
                """
                SELECT ticket_id, tienda_id, cliente_club, categoria, importe_eur, unidades
                FROM bronze.tickets_raw
                WHERE fecha_batch = %s
                ORDER BY id_ingesta;
                """,
                (ds,),
            )
            crudos = cur.fetchall()

            vistos: set[str] = set()
            validos: list[tuple[Any, ...]] = []
            cuarentena: list[tuple[Any, ...]] = []

            for ticket_id, tienda_id, socio, categoria, importe, unidades in crudos:
                if not ticket_id:
                    cuarentena.append((ds, ticket_id, tienda_id, importe, "ticket_id_nulo"))
                    continue
                if ticket_id in vistos:
                    cuarentena.append((ds, ticket_id, tienda_id, importe, "ticket_duplicado_tpv"))
                    continue
                vistos.add(ticket_id)

                if tienda_id not in tiendas_ok:
                    cuarentena.append((ds, ticket_id, tienda_id, importe, "tienda_desconocida"))
                    continue
                if importe is None or float(importe) <= 0:
                    cuarentena.append((ds, ticket_id, tienda_id, importe, "importe_no_positivo"))
                    continue
                if unidades is None or int(unidades) <= 0:
                    cuarentena.append((ds, ticket_id, tienda_id, importe, "unidades_invalidas"))
                    continue

                es_socio = str(socio).strip().upper() in {"SI", "1", "TRUE"}
                cat_limpia = (categoria or "SIN_CATEGORIA").strip().upper()
                validos.append((ticket_id, ds, tienda_id, es_socio, cat_limpia, importe, unidades))

            # Carga atómica e idempotente para `fecha_batch`
            cur.execute("DELETE FROM silver.tickets_clean WHERE fecha_batch = %s;", (ds,))
            cur.execute("DELETE FROM silver.tickets_quarantine WHERE fecha_batch = %s;", (ds,))

            cur.executemany(
                """
                INSERT INTO silver.tickets_clean
                    (ticket_id, fecha_batch, tienda_id, es_socio_club, categoria, importe_eur, unidades)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                validos,
            )
            cur.executemany(
                """
                INSERT INTO silver.tickets_quarantine
                    (fecha_batch, ticket_id, tienda_id, importe_eur, motivo_rechazo)
                VALUES (%s, %s, %s, %s, %s);
                """,
                cuarentena,
            )
            conn.commit()

        print(f"[SILVER] Fecha={ds} | Validos={len(validos)} | Cuarentena={len(cuarentena)}")
        return {
            "fecha_batch": ds,
            "filas_silver": len(validos),
            "filas_cuarentena": len(cuarentena),
        }

    @task(outlets=[ASSET_GOLD_VENTAS])
    def agregar_silver_a_gold(meta_silver: dict[str, Any]) -> dict[str, Any]:
        """Paso 3 (Gold): construye KPIs diarios por tienda y emite el Asset de Airflow 3."""
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        ds = meta_silver["fecha_batch"]
        hook = PostgresHook(postgres_conn_id="carrefour_pg")

        sql_gold = """
        DELETE FROM gold.ventas_diarias_tienda WHERE fecha_batch = %s;

        INSERT INTO gold.ventas_diarias_tienda (
            fecha_batch, tienda_id, nombre_tienda, formato,
            num_tickets, facturacion_eur, ticket_medio_eur, pct_socios_club
        )
        SELECT
            t.fecha_batch,
            t.tienda_id,
            d.nombre,
            d.formato,
            COUNT(*) AS num_tickets,
            ROUND(SUM(t.importe_eur), 2) AS facturacion_eur,
            ROUND(AVG(t.importe_eur), 2) AS ticket_medio_eur,
            ROUND(100.0 * AVG(CASE WHEN t.es_socio_club THEN 1.0 ELSE 0.0 END), 2) AS pct_socios_club
        FROM silver.tickets_clean AS t
        JOIN silver.dim_tiendas AS d ON d.tienda_id = t.tienda_id
        WHERE t.fecha_batch = %s
        GROUP BY t.fecha_batch, t.tienda_id, d.nombre, d.formato;
        """

        with hook.get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql_gold, (ds, ds))
            cur.execute(
                """
                SELECT tienda_id, num_tickets, facturacion_eur, ticket_medio_eur
                FROM gold.ventas_diarias_tienda
                WHERE fecha_batch = %s
                ORDER BY facturacion_eur DESC;
                """,
                (ds,),
            )
            resumen = cur.fetchall()
            conn.commit()

        print(f"[GOLD] Fecha={ds} | Tiendas agregadas={len(resumen)}")
        for tid, n_tkt, fact, medio in resumen:
            print(f"  - {tid}: {n_tkt} tickets | {fact} EUR | ticket medio {medio} EUR")

        return {"fecha_batch": ds, "tiendas_gold": len(resumen)}

    # Definición limpia del grafo en TaskFlow API (Airflow 3)
    meta_b = ingestar_batch_bronze()
    meta_s = refinar_bronze_a_silver(meta_b)
    agregar_silver_a_gold(meta_s)


carrefour_medallion_batch()
