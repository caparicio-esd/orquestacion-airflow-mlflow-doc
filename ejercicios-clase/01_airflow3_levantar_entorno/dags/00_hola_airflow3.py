"""
DAG 00 — Smoke test en Apache Airflow 3 (Task SDK).
Verifica que el entorno funciona y que la conexión `carrefour_pg` responde.
"""
from datetime import datetime
from airflow.sdk import dag, task


@dag(
    dag_id="hola_airflow3_carrefour",
    start_date=datetime(2026, 1, 1),
    schedule=None,  # Solo ejecución manual en el ejercicio de arranque
    catchup=False,
    tags=["clase", "airflow3", "carrefour", "setup"],
    doc_md="Comprueba el arranque de Airflow 3 y la conexión PostgreSQL `carrefour_pg`.",
)
def hola_airflow3_carrefour():
    @task
    def saludar() -> str:
        msg = "Entorno Apache Airflow 3 operativo para el laboratorio de Carrefour."
        print(msg)
        return msg

    @task
    def comprobar_bd_carrefour(mensaje_previo: str) -> int:
        from airflow.providers.postgres.hooks.postgres import PostgresHook

        print(f"Recibido por XCom: {mensaje_previo}")
        hook = PostgresHook(postgres_conn_id="carrefour_pg")
        tiendas = hook.get_records("SELECT tienda_id, nombre, formato FROM silver.dim_tiendas ORDER BY tienda_id;")
        print(f"Tiendas Carrefour registradas en PostgreSQL ({len(tiendas)}):")
        for tid, nombre, formato in tiendas:
            print(f"  - {tid} | {nombre} ({formato})")
        return len(tiendas)

    @task
    def resumen(total_tiendas: int) -> None:
        print(f"Verificación completada con éxito: {total_tiendas} tiendas disponibles.")

    resumen(comprobar_bd_carrefour(saludar()))


hola_airflow3_carrefour()
