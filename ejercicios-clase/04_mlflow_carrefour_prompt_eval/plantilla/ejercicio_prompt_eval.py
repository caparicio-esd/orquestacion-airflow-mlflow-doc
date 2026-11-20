"""
PLANTILLA PARA CLASE — Prompt Registry, Tracing y Evaluación con MLflow 3 (Carrefour).
Completa los `# TODO` en directo y explora los resultados en `mlflow ui`.
"""
import json
import sys
from pathlib import Path
from typing import Any

import mlflow
from mlflow.entities import Feedback
from mlflow.genai.scorers import scorer

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "solucion"))
from llm_backend import invocar_llm, recuperar_contexto

TRACKING_URI = f"sqlite:///{BASE_DIR / 'mlflow_genai_carrefour.db'}"
PROMPT_NAME = "carrefour_soporte_clase"


# TODO 1: Define un scorer personalizado con @scorer que compruebe que la respuesta
# incluye los términos en `expectations["must_include"]` y ninguno de `expectations["must_not_include"]`.
@scorer
def comprobar_hechos(*, outputs: str, expectations: dict[str, Any]) -> Feedback:
    raise NotImplementedError("Completa el scorer en clase")


def main() -> None:
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment("carrefour_prompt_eval_clase")

    # TODO 2: Registra una plantilla de prompt con `mlflow.genai.register_prompt(...)`
    # que acepte {{contexto}} y {{pregunta}} y obligue a citar códigos [POL-...].

    # TODO 3: Carga el dataset `golden_dataset_carrefour.json` en formato
    # [{"inputs": ..., "expectations": ...}, ...]

    # TODO 4: Crea una función `predict_fn(pregunta: str) -> str` decorada con `@mlflow.trace`
    # que recupere el contexto, formatee el prompt registrado y llame a `invocar_llm(..., forzar_offline=True)`.

    # TODO 5: Lanza `mlflow.genai.evaluate(data=..., predict_fn=..., scorers=[comprobar_hechos])`
    # dentro de `with mlflow.start_run(...):` y observa trazas y métricas en `mlflow ui`.
    print("Completa los TODO 1..5 y vuelve a ejecutar este script.")


if __name__ == "__main__":
    main()
