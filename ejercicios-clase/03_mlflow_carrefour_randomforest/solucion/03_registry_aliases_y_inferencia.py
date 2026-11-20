"""
SOLUCIÓN 03 — Promoción en MLflow Model Registry con Aliases (@champion) e inferencia.
Reemplaza el antiguo flujo deprecado de Stages (Staging/Production) por Aliases + Tags.
"""
from __future__ import annotations

from pathlib import Path

import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient

BASE_DIR = Path(__file__).resolve().parents[1]
TRACKING_URI = f"sqlite:///{BASE_DIR / 'mlflow_carrefour.db'}"
EXPERIMENT_NAME = "carrefour_club_churn_rf"
MODEL_NAME = "carrefour_churn_rf"
UMBRAL_MIN_F1 = 0.72


def main() -> None:
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient(tracking_uri=TRACKING_URI)

    exp = client.get_experiment_by_name(EXPERIMENT_NAME)
    if exp is None:
        raise RuntimeError("Ejecuta primero `02_mlflow_tracking_y_sweep.py` para generar runs.")

    # 1. Localizamos la mejor run del experimento ordenada por F1 descendente
    runs = client.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.f1 DESC"],
        max_results=1,
    )
    if not runs:
        raise RuntimeError("No hay runs registradas en el experimento.")

    mejor_run = runs[0]
    run_id = mejor_run.info.run_id
    mejor_f1 = mejor_run.data.metrics["f1"]
    mejor_auc = mejor_run.data.metrics["roc_auc"]
    print(f"Mejor run encontrada: {run_id[:8]} | F1={mejor_f1:.4f} | ROC-AUC={mejor_auc:.4f}")

    # 2. Quality gate antes de registrar/promocionar
    if mejor_f1 < UMBRAL_MIN_F1:
        raise ValueError(f"Calidad insuficiente: F1={mejor_f1:.4f} < umbral {UMBRAL_MIN_F1}")

    # 3. Registrar versión en el Model Registry
    model_uri = f"runs:/{run_id}/random_forest_model"
    mv = mlflow.register_model(model_uri=model_uri, name=MODEL_NAME)
    print(f"Modelo registrado: {MODEL_NAME} versión {mv.version}")

    # 4. Etiquetado de gobernanza y promoción moderna con ALIASES (no Stages)
    client.set_model_version_tag(MODEL_NAME, mv.version, "validation_status", "passed")
    client.set_model_version_tag(MODEL_NAME, mv.version, "f1_holdout", f"{mejor_f1:.4f}")

    # Si ya existía un @champion previo, lo guardamos en @previous_champion para rollback inmediato
    try:
        prev = client.get_model_version_by_alias(MODEL_NAME, "champion")
        if str(prev.version) != str(mv.version):
            client.set_registered_model_alias(MODEL_NAME, "previous_champion", prev.version)
    except Exception:
        pass

    client.set_registered_model_alias(MODEL_NAME, "champion", mv.version)
    print(f"Alias '@champion' apuntando ahora a {MODEL_NAME} v{mv.version}\n")

    # 5. Inferencia desacoplada cargando exclusivamente por alias
    modelo_prod = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}@champion")
    clientes_nuevos = pd.DataFrame(
        [
            {
                # Cliente en alto riesgo: lleva 52 días sin venir, 2 quejas, no usa la app
                "visitas_ultimo_mes": 1.0,
                "ticket_medio_eur": 23.5,
                "dias_desde_ultima_compra": 52.0,
                "cheque_ahorro_eur": 1.8,
                "usa_app_mi_carrefour": 0.0,
                "compra_online_drive": 0.0,
                "quejas_90d": 2.0,
                "antiguedad_meses": 6.0,
            },
            {
                # Cliente fiel: compra cada semana, usa App Mi Carrefour y Drive, 0 quejas
                "visitas_ultimo_mes": 7.0,
                "ticket_medio_eur": 84.0,
                "dias_desde_ultima_compra": 4.0,
                "cheque_ahorro_eur": 14.5,
                "usa_app_mi_carrefour": 1.0,
                "compra_online_drive": 1.0,
                "quejas_90d": 0.0,
                "antiguedad_meses": 48.0,
            },
        ]
    )

    preds = modelo_prod.predict(clientes_nuevos)
    for idx, pred in enumerate(preds, 1):
        etiqueta = "ALTO RIESGO DE ABANDONO -> Enviar cupón ChequeAhorro" if pred == 1 else "CLIENTE FIDELIZADO"
        print(f"  Cliente {idx}: predicción={pred} ({etiqueta})")


if __name__ == "__main__":
    main()
