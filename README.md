# Manual Técnico: Orquestación de Datos, MLOps y LLMOps (Apache Airflow y MLflow)

Documentación técnica ampliada y modernizada en **LaTeX** y **PDF**, basada en la presentación *Orquestación y pipelines de datos: Airflow y MLflow* (Ingeniería Big Data en la Nube — DIT, Universidad Politécnica de Madrid), extendida en profundidad con:

- **Apache Airflow 2.10 y 3.0+:** arquitectura orientada a servicios, Task SDK, DAG Versioning, Assets, backfills nativos y patrones avanzados de DAGs.
- **Conectividad y Conectores de Airflow:** Providers, Connections, Secrets Backends (AWS Secrets Manager, Vault, GCP, Azure), Hooks, Deferrable Operators, `SQLExecuteQueryOperator`, `ObjectStoragePath`, REST/OAuth2, Spark, dbt/Cosmos, KubernetesPodOperator, Kafka, OpenLineage y desarrollo de conectores propios.
- **MLOps y MLflow Clásico:** ciclo de vida completo en 11 etapas, Feature Stores, Data/Concept Drift, Tracking, Models (`pyfunc`), Model Registry (Aliases vs. Stages), despliegue progresivo y CI/CD para ML.
- **Modernización LLMOps con MLflow 3:** experimentación sistemática de Prompt Engineering, Prompt Registry, optimización automática de prompts (DSPy y GEPA), Tracing compatible con OpenTelemetry, evaluación LLM/RAG (`mlflow.genai.evaluate`, LLM-as-a-Judge), `ResponsesAgent`, AI Gateway y monitorización continua.
- **Integración End-to-End Airflow + MLflow:** dos arquitecturas completas de producción (pipeline MLOps tabular con detección de drift y pipeline LLMOps/RAG con Airflow 3 Assets y MLflow 3).

## Estructura del proyecto

- `orquestacion-airflow-mlflow-manual.pdf`: documento compilado (~197 páginas A4) listo para lectura e impresión.
- `main.tex`: fichero raíz que ensambla todas las partes, capítulos y apéndices.
- `preamble.tex`: estilos tipográficos, paleta de colores, entornos `tcolorbox`, `listings` y estilos TikZ/PGFPlots.
- `chapters/`: ficheros modulares `.tex` por capítulo (`00_prefacio.tex` a `10_integracion_airflow_mlflow.tex`, y apéndices `A`, `B`, `C`).
- `ejercicios-clase/`: **4 mini-ejercicios cortos y autocontenidos para clase** (temática Carrefour, Airflow 3, PostgreSQL Medallion por batches, RandomForest con MLflow 3 y Prompt Engineering + evaluación con `mlflow.genai.evaluate`), cada uno con `plantilla/`, `solucion/` y `README.md`.
- `presentacion-clase/index.html`: **presentación única y 100 % autocontenida en un solo archivo HTML (150 KB, 46 diapositivas lineales)** para clase de 2 horas, con 16 ilustraciones vectoriales SVG con animaciones suaves de flujo, *syntax highlighting* offline, tema oscuro/claro (`T`) y pantalla completa (`F`).
- `Makefile`: automatización de la compilación.

## Cómo recompilar el PDF

Con **Tectonic** (recomendado, resuelve paquetes automáticamente):

```bash
make
# o directamente:
tectonic -X compile main.tex
```

Con **XeLaTeX** o **LuaLaTeX** (TeX Live / MacTeX / Overleaf):

```bash
xelatex main.tex
xelatex main.tex
```
