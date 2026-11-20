"""
SOLUCIÓN 01 — Entrenamiento baseline de RandomForest SIN MLflow.
Punto de partida docente para mostrar qué falta cuando no hay experiment tracking.
"""
import argparse
import sys
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datos_carrefour import generar_dataset_club_carrefour


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_estimators", type=int, default=100)
    parser.add_argument("--max_depth", type=int, default=8)
    args = parser.parse_args()

    df = generar_dataset_club_carrefour(n_clientes=2500, seed=42)
    X = df.drop(columns=["abandono"])
    y = df["abandono"]

    # Split estratificado para preservar la proporción de abandono
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )

    model = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print(f"RandomForest(n_estimators={args.n_estimators}, max_depth={args.max_depth})")
    print(f"  Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"  Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"  Recall   : {recall_score(y_test, y_pred):.4f}")
    print(f"  F1-score : {f1_score(y_test, y_pred):.4f}")
    print(f"  ROC-AUC  : {roc_auc_score(y_test, y_prob):.4f}")


if __name__ == "__main__":
    main()
