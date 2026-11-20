"""
SOLUCIÓN 02 — Experimentación reproducible de RandomForest con MLflow 3 Tracking.
Lanza un mini-sweep de 6 configuraciones, registra parámetros, métricas, dataset,
matriz de confusión como artefacto PNG y el modelo con firma tipada.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.data
import mlflow.sklearn
from mlflow.models import infer_signature
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
from datos_carrefour import generar_dataset_club_carrefour

TRACKING_URI = f"sqlite:///{BASE_DIR / 'mlflow_carrefour.db'}"
ARTIFACT_LOCATION = (BASE_DIR / "mlartifacts").as_uri()
EXPERIMENT_NAME = "carrefour_club_churn_rf"


def main() -> None:
    mlflow.set_tracking_uri(TRACKING_URI)
    if mlflow.get_experiment_by_name(EXPERIMENT_NAME) is None:
        mlflow.create_experiment(EXPERIMENT_NAME, artifact_location=ARTIFACT_LOCATION)
    mlflow.set_experiment(EXPERIMENT_NAME)

    df = generar_dataset_club_carrefour(n_clientes=2500, seed=42)
    X = df.drop(columns=["abandono"])
    y = df["abandono"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )

    dataset_train = mlflow.data.from_pandas(
        X_train.assign(abandono=y_train),
        name="club_carrefour_clientes_v1",
        targets="abandono",
    )

    grid = [
        (50, 4),
        (50, 8),
        (50, 14),
        (150, 4),
        (150, 8),
        (150, 14),
    ]

    print(f"Tracking URI: {TRACKING_URI} | Experimento: {EXPERIMENT_NAME}\n")

    for n_estimators, max_depth in grid:
        run_name = f"rf_trees{n_estimators}_depth{max_depth}"
        with mlflow.start_run(run_name=run_name) as run:
            mlflow.set_tags(
                {
                    "caso_uso": "churn_club_carrefour",
                    "algoritmo": "RandomForestClassifier",
                    "equipo": "clase-bigdata-upm",
                }
            )
            mlflow.log_input(dataset_train, context="training")

            # 1. Hiperparámetros -> SIEMPRE con log_param / log_params
            params = {
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "class_weight": "balanced",
                "random_state": 42,
                "test_size": 0.25,
            }
            mlflow.log_params(params)

            # 2. Entrenamiento
            model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X_train, y_train)

            # 3. Evaluación sobre el conjunto holdout (test)
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1]
            metrics = {
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "precision": float(precision_score(y_test, y_pred)),
                "recall": float(recall_score(y_test, y_pred)),
                "f1": float(f1_score(y_test, y_pred)),
                "roc_auc": float(roc_auc_score(y_test, y_prob)),
            }
            # IMPORTANTE: las métricas numéricas SIEMPRE con log_metric / log_metrics (no log_param)
            mlflow.log_metrics(metrics)

            # 4. Artefacto visual: matriz de confusión
            cm = confusion_matrix(y_test, y_pred)
            fig, ax = plt.subplots(figsize=(4.5, 4.0))
            ConfusionMatrixDisplay(cm, display_labels=["Activo", "Abandono"]).plot(ax=ax, cmap="Blues")
            ax.set_title(f"Carrefour Churn — {run_name}")
            fig.tight_layout()
            with tempfile.TemporaryDirectory() as tmpdir:
                cm_path = Path(tmpdir) / "matriz_confusion.png"
                fig.savefig(cm_path, dpi=120)
                mlflow.log_artifact(str(cm_path), artifact_path="evaluacion")
            plt.close(fig)

            # 5. Guardar el modelo con firma estricta e input_example
            # En MLflow 3.18+ skops exige declarar explícitamente los tipos de árbol de confianza
            signature = infer_signature(X_train, model.predict(X_train))
            mlflow.sklearn.log_model(
                sk_model=model,
                name="random_forest_model",
                signature=signature,
                input_example=X_test.head(3),
                skops_trusted_types=["sklearn.tree._tree.Tree"],
            )

            print(
                f"Run {run.info.run_id[:8]} | {run_name:<20} | "
                f"F1={metrics['f1']:.4f} | Recall={metrics['recall']:.4f} | AUC={metrics['roc_auc']:.4f}"
            )

    print("\nSweep finalizado. Abre la UI con:")
    print(f"  mlflow ui --backend-store-uri {TRACKING_URI} --port 5000")


if __name__ == "__main__":
    main()
