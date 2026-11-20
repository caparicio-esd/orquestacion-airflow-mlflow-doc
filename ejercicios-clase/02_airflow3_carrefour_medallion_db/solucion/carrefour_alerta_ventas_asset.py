"""
SOLUCIÓN — DAG 2: Monitorización reactiva disparada por Asset (Airflow 3).
Se ejecuta automáticamente en cuanto `carrefour_medallion_batch` actualiza
la tabla `gold.ventas_diarias_tienda`, sin depender de horarios cron acoplados.
"""
from __future__ import annotations

from datetime import datetime
from airflow.sdk import Asset, dag, task

ASSET_GOLD_VENTAS = Asset("postgres://carrefour_dw/gold/ventas_diarias_tienda")
UMBRAL_FACTURACION_MIN_EUR = 600.0


@dag(
    dag_id="carrefour_alerta_ventas_asset",
    start_date=datetime(2026, 1, 1),
    schedule=[ASSET_GOLD_VENTAS],  # Asset-Driven Scheduling nativo en Airflow 3
    catchup=False,
    tags=["clase", "airflow3", "carrefour", "asset"],
    doc_md="DAG reactivo disparado cuando se actualiza el Asset Gold de ventas Carrefour.",
)
def carrefour_alerta_ventas_asset():
    @task
    def auditar_ventas_y_generar_alertas() -> int:
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        hook = PostgresHook(postgres_conn_id="carrefour_pg")
        with hook.get_conn() as conn, conn.cursor() as cur:
            # Tomamos la fecha más reciente materializada en Gold
            cur.execute("SELECT MAX(fecha_batch) FROM gold.ventas_diarias_tienda;")
            ultima_fecha = cur.fetchone()[0]
            if ultima_fecha is None:
                print("Aún no existen datos en gold.ventas_diarias_tienda.")
                return 0

            cur.execute(
                """
                SELECT tienda_id, nombre_tienda, facturacion_eur, num_tickets
                FROM gold.ventas_diarias_tienda
                WHERE fecha_batch = %s;
                """,
                (ultima_fecha,),
            )
            filas = cur.fetchall()

            # Idempotencia: sustituimos las alertas de esa fecha
            cur.execute("DELETE FROM gold.alertas_operativas WHERE fecha_batch = %s;", (ultima_fecha,))

            alertas = 0
            for tienda_id, nombre, facturacion, num_tickets in filas:
                if float(facturacion) < UMBRAL_FACTURACION_MIN_EUR:
                    msg = (
                        f"{nombre} ({tienda_id}) facturó {facturacion} EUR "
                        f"({num_tickets} tickets), por debajo del umbral de {UMBRAL_FACTURACION_MIN_EUR} EUR."
                    )
                    cur.execute(
                        """
                        INSERT INTO gold.alertas_operativas (fecha_batch, tienda_id, severidad, mensaje)
                        VALUES (%s, %s, %s, %s);
                        """,
                        (ultima_fecha, tienda_id, "WARNING", msg),
                    )
                    print(f"[ALERTA] {msg}")
                    alertas += 1

            conn.commit()

        print(f"Auditoría completada para {ultima_fecha}: {alertas} alertas registradas.")
        return alertas

    auditar_ventas_y_generar_alertas()


carrefour_alerta_ventas_asset()
