"""
PLANTILLA PARA CLASE — RandomForest (Churn Club Carrefour) con MLflow 3.
Completa los `# TODO` para registrar experimentos y promocionar el mejor modelo.
"""
import sys
from pathlib import Path

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
from datos_carrefour import generar_dataset_club_carrefour

TRACKING_URI = f"sqlite:///{BASE_DIR / 'mlflow_carrefour.db'}"


def main() -> None:
    mlflow.set_tracking_uri(TRACKING_URI)
    # TODO 1: Configura el experimento "carrefour_club_churn_rf"

    df = generar_dataset_club_carrefour(n_clientes=2500, seed=42)
    X = df.drop(columns=["abandono"])
    y = df["abandono"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )

    for n_estimators, max_depth in [(50, 4), (100, 8), (150, 12)]:
        # TODO 2: Abre una run con `with mlflow.start_run(run_name=...) as run:`
        # TODO 3: Registra los hiperparámetros con `mlflow.log_params(...)`
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight="balanced",
            random_state=42,
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        # TODO 4: Calcula accuracy, recall, f1 y roc_auc y regístralas con `mlflow.log_metrics(...)`
        # (Recuerda: ¡NUNCA uses log_param para métricas numéricas!)
        # TODO 5: Registra el modelo con firma (`infer_signature`) mediante `mlflow.sklearn.log_model(...)`
        # Nota MLflow 3.18+: pasa `skops_trusted_types=["sklearn.tree._tree.Tree"]` para serialización segura.
        print(f"Entrenado n_estimators={n_estimators}, max_depth={max_depth}, f1={f1_score(y_test, y_pred):.4f}")

    # TODO 6 (Bonus): Con MlflowClient busca la mejor run por `metrics.f1 DESC`,
    # regístrala con `mlflow.register_model(...)` y asígnale el alias `@champion`.


if __name__ == "__main__":
    main()
