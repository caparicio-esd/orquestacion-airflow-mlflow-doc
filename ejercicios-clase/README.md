# Mini-Ejercicios Autocontenidos para Clase (Caso Carrefour)

Colección de **4 laboratorios cortos, progresivos y autocontenidos** diseñados para ejecutarse en directo en el aula (20--30 min cada uno), todos ambientados en un mismo hilo conductor realista: **operaciones y analítica de tiendas Carrefour** (tickets TPV, refinado por lotes Medallion, fidelización Club Carrefour y asistente de atención al cliente con LLMs).

Todos los ejercicios emplean las versiones modernas de referencia en 2025--2026:
- **Apache Airflow 3** (`from airflow.sdk import dag, task, Asset`, `api-server`, `dag-processor`, `SimpleAuthManager`, `SQLExecuteQueryOperator` / `PostgresHook`).
- **MLflow 3** (`mlflow.sklearn`, firmas `infer_signature`, Model Registry con **Aliases** `@champion`/`@challenger`, **Prompt Registry** `mlflow.genai.register_prompt`, **Tracing** `@mlflow.trace` y **Evaluación GenAI** `mlflow.genai.evaluate` con `@scorer`).

---

## Mapa de ejercicios y tiempos sugeridos

| Carpeta | Tema | Duración | Qué aprende el alumno |
| :--- | :--- | :---: | :--- |
| [`01_airflow3_levantar_entorno/`](./01_airflow3_levantar_entorno/) | Levantar Airflow 3 + PostgreSQL Carrefour | 15 min | Arquitectura Airflow 3, `docker compose` mínimo (2 contenedores) o `uv` + `airflow standalone`, Connections por variable de entorno y primer DAG con Task SDK. |
| [`02_airflow3_carrefour_medallion_db/`](./02_airflow3_carrefour_medallion_db/) | Refinado por batches Carrefour (Bronze $\to$ Silver $\to$ Gold) en DB | 30 min | TaskFlow API (`@dag`, `@task`), `PostgresHook`, limpieza/cuarentena, carga **idempotente** por fecha `{{ ds }}`, paso de referencias por XCom y programación reactiva con **`Asset`** de Airflow 3. |
| [`03_mlflow_carrefour_randomforest/`](./03_mlflow_carrefour_randomforest/) | Entrenamiento RandomForest (Churn Club Carrefour) con MLflow | 25 min | Evolución de baseline scikit-learn a MLflow Tracking (`log_metric` vs. `log_param`), barrido de hiperparámetros, artefactos (matriz de confusión), Model Registry con **Aliases** y serving REST. |
| [`04_mlflow_carrefour_prompt_eval/`](./04_mlflow_carrefour_prompt_eval/) | Prompt Engineering y Evaluación LLM (Soporte Carrefour) con MLflow 3 | 30 min | Versionado en **Prompt Registry** (`v1` $\to$ `v3`), trazabilidad `@mlflow.trace`, evaluación con `mlflow.genai.evaluate()` + `@scorer` (+ LLM-as-a-Judge opcional) y promoción automática del alias `@production`. Funciona con OpenAI, Ollama **o 100 % offline sin API key**. |

---

## Cómo usar `plantilla/` y `solucion/` en clase

Cada ejercicio práctico (02, 03 y 04) incluye dos subcarpetas:
- **`plantilla/`**: código con marcas `# TODO` listas para proyectar y completar en vivo con los alumnos.
- **`solucion/`**: implementación completa, probada y comentada para contrastar o lanzar directamente si falta tiempo.

## Prerrequisitos mínimos

- **Ejercicios 01 y 02 (Airflow 3):** Docker Desktop (opción recomendada, 1 comando) **o** Python 3.10--3.12 con `uv` / `venv`.
- **Ejercicios 03 y 04 (MLflow 3):** Python 3.10--3.12 (`uv` o `pip`). No requieren descarga de datasets externos ni clave API obligatoria (el ejercicio 04 incluye un modo `--offline` determinista para garantizar que la demo jamás falle en el aula).
