"""
PLANTILLA PARA CLASE — DAG 2: Alerta reactiva con Asset de Airflow 3.
"""
from datetime import datetime
from airflow.sdk import Asset, dag, task

ASSET_GOLD_VENTAS = Asset("postgres://carrefour_dw/gold/ventas_diarias_tienda")


# TODO 1: Cambia `schedule=None` por `schedule=[ASSET_GOLD_VENTAS]` para activar el disparo reactivo
@dag(
    dag_id="carrefour_alerta_ventas_asset",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["clase", "airflow3", "carrefour", "asset"],
)
def carrefour_alerta_ventas_asset():
    @task
    def auditar_ventas_y_generar_alertas() -> int:
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        hook = PostgresHook(postgres_conn_id="carrefour_pg")
        # TODO 2: Consulta la última fecha de `gold.ventas_diarias_tienda` e inserta una alerta
        # en `gold.alertas_operativas` para toda tienda con facturación < 600 EUR.
        raise NotImplementedError("Completa la auditoría reactiva en clase")

    auditar_ventas_y_generar_alertas()


carrefour_alerta_ventas_asset()
