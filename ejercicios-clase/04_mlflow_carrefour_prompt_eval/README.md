# Ejercicio 04 — Prompt Engineering, Prompt Registry y Evaluación LLM con MLflow 3 (Soporte Carrefour)

**Objetivo:** Modernizar el bloque de MLOps hacia **LLMOps** aplicando ingeniería experimental rigurosa sobre un **asistente de atención al cliente de Carrefour**:
1. Versionar plantillas de prompts de forma inmutable en el **MLflow Prompt Registry** (`v1` $\to$ `v2` $\to$ `v3`) y gestionar aliases (`@staging`, `@production`).
2. Trazar cada llamada (recuperación de política + generación LLM) con **MLflow Tracing** (`@mlflow.trace`).
3. Evaluar objetivamente las tres versiones sobre un **Golden Dataset** (incluyendo casos límite y ataques de *prompt injection*) mediante **`mlflow.genai.evaluate()`** y scorers `@scorer` (+ *LLM-as-a-Judge* opcional).
4. Promocionar automáticamente el alias **`@production`** solo si la versión candidata supera los *quality gates*.

---

## Preparación del entorno

```bash
cd ejercicios-clase/04_mlflow_carrefour_prompt_eval

uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

### Modos de ejecución (¡jamás falla en clase!)

| Modo | Cómo activarlo | Cuándo usarlo |
| :--- | :--- | :--- |
| **Offline determinista** (por defecto si no hay API key) | No requiere nada (o `--offline`) | Demostraciones sin WiFi o sin coste de API; reproduce de forma realista los fallos de `v1`/`v2` y el acierto de `v3`, poblando completamente Prompts, Traces y Evaluations en `mlflow ui`. |
| **OpenAI real** | `export OPENAI_API_KEY="sk-..."` | Evaluación en vivo con `gpt-4o-mini` + juez LLM-as-a-Judge (`Guidelines`). |
| **Ollama local (gratis)** | `export OPENAI_BASE_URL="http://localhost:11434/v1"`<br>`export OPENAI_API_KEY="ollama"`<br>`export LLM_MODEL="llama3.2"` | Modelos abiertos locales en tu portátil sin enviar datos fuera. |

---

## Guión de ejecución paso a paso en clase

### Paso 1 — Registrar 3 versiones progresivas en MLflow Prompt Registry
```bash
python solucion/01_prompt_registry.py
```
Registra `carrefour_soporte_cliente`:
- **`v1` (ingenua):** instrucciones vagas, sin política inyectada ni defensa contra inyección.
- **`v2` (con política):** incorpora el contexto de políticas oficiales Carrefour, pero sin citas obligatorias ni blindaje frente a manipulación.
- **`v3` (producción):** delimitación explícita de datos no confiables, cita obligatoria `[POL-...]`, rechazo de *out-of-scope* y defensa frente a *prompt injection*.

### Paso 2 — Ejecutar evaluación comparativa + Tracing + Promoción automática
```bash
python solucion/02_prompt_eval_y_tracing.py
```
Para cada versión (`v1`, `v2`, `v3`), el script:
- Carga el prompt directamente desde el registro (`prompts:/carrefour_soporte_cliente/<v>`).
- Ejecuta **`mlflow.genai.evaluate()`** sobre los 8 casos de `golden_dataset_carrefour.json`.
- Genera **trazas anidadas** (`asistente_carrefour` -> `buscar_politica` -> `generar_respuesta_llm`).
- Evalúa 4 métricas objetivas (`hechos_esperados`, `cita_politica`, `resistencia_inyeccion`, `concision`) y, si `OPENAI_API_KEY` está configurada, añade un juez **LLM-as-a-Judge** (`Guidelines`).
- Promociona la mejor versión al alias **`@production`** solo si cumple `resistencia_inyeccion == 1.0` y puntuación media $\ge 0.85$.

### Paso 3 — Inspeccionar Prompts, Trazas y Evaluaciones en MLflow 3 UI
```bash
mlflow ui --backend-store-uri sqlite:///mlflow_genai_carrefour.db --port 5002
```
Abre [http://localhost:5002](http://localhost:5002) y muestra en directo:
- Pestaña **Prompts**: diff entre `v1`, `v2` y `v3` y dónde apunta `@production`.
- Pestaña **Traces**: árbol de spans (`RETRIEVER` + `LLM`), latencia y tokens por consulta.
- Pestaña **Evaluations / Runs**: tabla comparativa de puntuaciones donde `v3` derrota claramente a `v1` y `v2`.

---

## Para practicar en directo con los alumnos
Abre [`plantilla/ejercicio_prompt_eval.py`](./plantilla/ejercicio_prompt_eval.py) y completa los `# TODO`.
