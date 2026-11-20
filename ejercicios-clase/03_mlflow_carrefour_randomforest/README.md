# Ejercicio 03 — Entrenamiento de RandomForest con MLflow 3 (Churn Club Carrefour)

**Objetivo:** Recorrer en directo la evolución completa de un modelo de Machine Learning clásico (**`RandomForestClassifier`**) para predecir el **abandono (*churn*) de socios del Club Carrefour**, desde un script sin trazabilidad hasta un flujo profesional con **MLflow Tracking**, artefactos, firmas y **Model Registry basado en Aliases** (`@challenger` -> `@champion`).

---

## Preparación rápida del entorno

```bash
cd ejercicios-clase/03_mlflow_carrefour_randomforest

# Con uv (recomendado, ~10 segundos)
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt

# O con python3 -m venv tradicional:
# python3 -m venv .venv && source .venv/bin/activate
# pip install -r requirements.txt
```

---

## Guión de ejecución paso a paso en clase

### Paso 1 — Baseline sin MLflow
```bash
python solucion/01_baseline_sin_mlflow.py
```
*Idea docente:* si cambias `n_estimators` o `max_depth` cinco veces, pierdes el rastro de qué configuración dio el mejor `F1` y no queda guardado el modelo ni el dataset exacto.

### Paso 2 — Instrumentar con MLflow Tracking y lanzar un mini-sweep
```bash
python solucion/02_mlflow_tracking_y_sweep.py
```
Este script ejecuta **6 runs** (`n_estimators` $\in \{50, 150\}$ $\times$ `max_depth` $\in \{4, 8, 14\}$) usando un almacén local SQLite (`sqlite:///mlflow_carrefour.db`) para soportar tanto Tracking como Model Registry moderno. Registra:
- Parámetros (`log_param`) separados correctamente de métricas (`log_metric`).
- Dataset de entrenamiento (`mlflow.data.from_pandas`).
- Gráfica de matriz de confusión como artefacto PNG (`log_artifact`).
- Modelo con firma tipada (`infer_signature`) e `input_example`.

### Paso 3 — Explorar las runs en la UI de MLflow
En otra terminal:
```bash
mlflow ui --backend-store-uri sqlite:///mlflow_carrefour.db --port 5000
```
Abre [http://localhost:5000](http://localhost:5000) y enseña en directo:
- La tabla comparativa filtrando por `metrics.f1 > 0.70`.
- La vista **Chart** (coordenadas paralelas `max_depth` / `n_estimators` -> `f1` y `roc_auc`).
- Los artefactos de cada run (`MLmodel`, `requirements.txt`, `matriz_confusion.png`).

### Paso 4 — Model Registry con Aliases (`@champion`) e inferencia desacoplada
```bash
python solucion/03_registry_aliases_y_inferencia.py
```
Selecciona la mejor run, aplica un *quality gate*, registra el modelo `carrefour_churn_rf`, le asigna el alias **`@champion`** y predice el riesgo de abandono de dos clientes nuevos cargando el modelo exclusivamente por su URI de alias (`models:/carrefour_churn_rf@champion`).

### Paso 5 (Bonus) — Servir el modelo como API REST
```bash
MLFLOW_TRACKING_URI=sqlite:///mlflow_carrefour.db \
  mlflow models serve -m "models:/carrefour_churn_rf@champion" -p 5001 --no-conda

# En otra terminal:
curl -X POST http://localhost:5001/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "dataframe_records": [
      {
        "visitas_ultimo_mes": 1,
        "ticket_medio_eur": 24.5,
        "dias_desde_ultima_compra": 48,
        "cheque_ahorro_eur": 3.2,
        "usa_app_mi_carrefour": 0,
        "compra_online_drive": 0,
        "quejas_90d": 2,
        "antiguedad_meses": 8
      }
    ]
  }'
```

---

## Para practicar en directo con los alumnos
Abre [`plantilla/ejercicio_rf_mlflow.py`](./plantilla/ejercicio_rf_mlflow.py) y completa los `# TODO` en clase.
