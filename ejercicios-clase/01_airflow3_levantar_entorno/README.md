# Ejercicio 01 — Levantar un entorno sencillo de Apache Airflow 3 + PostgreSQL (Carrefour)

**Objetivo:** Poner en marcha en menos de 2 minutos un entorno moderno de **Apache Airflow 3** conectado a una base de datos **PostgreSQL** preparada para el caso práctico de tiendas **Carrefour** (esquemas `bronze`, `silver`, `gold`), y ejecutar un primer DAG de verificación con el nuevo **Task SDK** (`from airflow.sdk import dag, task`).

---

## Opción A (Recomendada para clase): Docker Compose mínimo (2 contenedores)

Este `docker-compose.yml` arranca únicamente dos servicios:
1. **`postgres` (PostgreSQL 16):** aloja la base de metadatos `airflow` y la base de datos analítica `carrefour_dw` (inicializada automáticamente por `init_carrefour_db.sql`).
2. **`airflow` (`apache/airflow:3.1.0` en modo `standalone` con `LocalExecutor`):** levanta automáticamente `api-server` (UI React en puerto `8080`), `scheduler`, `dag-processor` y `triggerer`, con la conexión **`carrefour_pg`** ya registrada mediante `AIRFLOW_CONN_CARREFOUR_PG`.

### Pasos en clase

```bash
cd ejercicios-clase/01_airflow3_levantar_entorno

# 1. Levantar Postgres + Airflow 3
docker compose up -d

# 2. Esperar ~25-40 segundos y verificar que todo responde
./verificar_entorno.sh
```

- **UI React de Airflow 3:** abrir [http://localhost:8080](http://localhost:8080) (acceso directo sin contraseña gracias a `AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS=True`, pensado exclusivamente para laboratorio local).
- **Ver el DAG de prueba:** buscar **`hola_airflow3_carrefour`**, activarlo (*Unpause*) y lanzarlo manualmente (*Trigger DAG*).
- **Parar al terminar la clase:**
  ```bash
  docker compose down        # conserva datos de Postgres
  docker compose down -v     # limpia también el volumen de BD
  ```

---

## Opción B (Sin Docker): Instalación local rápida con `uv` + `airflow standalone`

Si prefieres ejecutar Airflow 3 directamente en tu portátil sin Docker:

```bash
cd ejercicios-clase/01_airflow3_levantar_entorno

uv venv .venv --python 3.12
source .venv/bin/activate

AIRFLOW_VERSION=3.1.0
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.12.txt"
uv pip install "apache-airflow==${AIRFLOW_VERSION}" apache-airflow-providers-postgres --constraint "${CONSTRAINT_URL}"

export AIRFLOW_HOME="$PWD/.airflow_local"
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS=True

airflow standalone
```

---

## Qué enseñar en este bloque (puntos clave de Airflow 3)

1. **Nueva UI React y `api-server`:** en Airflow 3 desaparece el viejo `webserver` basado en Flask; ahora todo pasa por FastAPI (`api-server`) y una interfaz React con vista dual **Tasks / Assets**.
2. **Nuevo Task SDK (`airflow.sdk`):** observar en `dags/00_hola_airflow3.py` cómo las importaciones ya no vienen de `airflow.decorators` ni `airflow.utils.dates.days_ago`, sino de `from airflow.sdk import dag, task` y fechas explícitas con `pendulum` o `datetime`.
3. **Conexión sin credenciales en código:** mostrar en la terminal cómo la variable `AIRFLOW_CONN_CARREFOUR_PG` inyecta la conexión a PostgreSQL sin hardcodear ninguna contraseña en los DAGs.
