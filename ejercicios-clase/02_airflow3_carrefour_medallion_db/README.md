# Ejercicio 02 — Refinado por Batches Carrefour (Bronze -> Silver -> Gold) con Airflow 3 y PostgreSQL

**Objetivo:** Construir un pipeline **Medallion por lotes (batches)** en **Apache Airflow 3** usando el nuevo **Task SDK** (`from airflow.sdk import dag, task, Asset`), **Connections + `PostgresHook`**, escritura **idempotente** particionada por fecha lógica (`ds`) y un segundo DAG reactivo disparado mediante un **`Asset`**.

---

## Escenario de negocio (Carrefour)

Cada noche, las cajas (TPV) de 5 tiendas Carrefour generan un lote de tickets. Como ocurre en cualquier sistema real, el lote crudo llega con **problemas de calidad**:
- **Duplicados** por reintentos de red de los TPV (`ticket_id` repetido).
- **Importes negativos o nulos** (devoluciones mal codificadas o errores de escáner).
- **Tiendas desconocidas** que no existen en el catálogo maestro `silver.dim_tiendas`.
- **Categorías sin normalizar** (`"  frescos "`, `"ELECTRONICA"`, `None`).

El DAG realiza el refinado progresivo en tres tareas:
1. **`ingestar_batch_bronze`**: inserta el lote crudo del día `{{ ds }}` en `bronze.tickets_raw` (borrando previamente solo esa fecha para mantener reejecutabilidad limpia) y devuelve por XCom únicamente un diccionario ligero con metadatos (`fecha`, `filas_raw`).
2. **`refinar_bronze_a_silver`**: separa los tickets válidos de los inválidos, normaliza texto y banderas de socio Club Carrefour, elimina duplicados, envía los registros erróneos a `silver.tickets_quarantine` y carga los válidos en `silver.tickets_clean` de forma **idempotente** (`DELETE` por `fecha_batch` + `INSERT` en la misma transacción).
3. **`agregar_silver_a_gold`**: calcula los KPIs diarios por tienda en `gold.ventas_diarias_tienda` (`num_tickets`, `facturacion_eur`, `ticket_medio_eur`, `pct_socios_club`) y declara `outlets=[ASSET_GOLD_VENTAS]`.

En cuanto finaliza el paso 3, Airflow 3 dispara automáticamente el segundo DAG **`carrefour_alerta_ventas_asset`**, que revisa la capa Gold y guarda alertas en `gold.alertas_operativas` si alguna tienda cae por debajo del umbral diario.

---

## Cómo ejecutarlo en clase

### 1. Probar con Airflow 3 (usando el entorno del Ejercicio 01)

```bash
# Opción A: Copiar las plantillas (para rellenar los # TODO en vivo)
cp plantilla/*.py ../01_airflow3_levantar_entorno/dags/

# Opción B: Copiar las soluciones listas para ejecutar
cp solucion/*.py ../01_airflow3_levantar_entorno/dags/
```

1. Abre [http://localhost:8080](http://localhost:8080).
2. Activa (*Unpause*) ambos DAGs: `carrefour_medallion_batch` y `carrefour_alerta_ventas_asset`.
3. Lanza manualmente `carrefour_medallion_batch` (*Trigger DAG*).
4. Observa en la pestaña **Assets** cómo al terminar `agregar_silver_a_gold` se dispara automáticamente `carrefour_alerta_ventas_asset`.
5. **Prueba de idempotencia en clase:** vuelve a lanzar el DAG para la **misma fecha** y comprueba en PostgreSQL que **no hay duplicados**:

```bash
docker exec clase-carrefour-postgres psql -U airflow -d carrefour_dw -c \
  "SELECT fecha_batch, tienda_id, nombre_tienda, num_tickets, facturacion_eur, pct_socios_club
   FROM gold.ventas_diarias_tienda ORDER BY fecha_batch, facturacion_eur DESC;"

docker exec clase-carrefour-postgres psql -U airflow -d carrefour_dw -c \
  "SELECT fecha_batch, ticket_id, motivo_rechazo FROM silver.tickets_quarantine;"

docker exec clase-carrefour-postgres psql -U airflow -d carrefour_dw -c \
  "SELECT fecha_batch, tienda_id, severidad, mensaje FROM gold.alertas_operativas;"
```

### 2. Prueba rápida sin Docker ni Airflow (2 segundos)

```bash
python3 probar_logica_sin_airflow.py
```

---

## Retos propuestos para los alumnos

1. Añadir una tarea intermedia con `@task.branch` que envíe una alerta de calidad si la tasa de cuarentena supera el 20 % del lote.
2. Cambiar la consulta de `agregar_silver_a_gold` para usar `SQLExecuteQueryOperator` cargando un fichero `.sql` externo.
3. Ejecutar un **Backfill** de 3 días seguidos desde la UI de Airflow 3 y comprobar la partición por `fecha_batch` en `gold.ventas_diarias_tienda`.
