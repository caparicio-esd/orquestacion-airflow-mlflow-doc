"""
Generador sintético reproducible de clientes del Club Carrefour para clase.
Sin descargas externas: funciona 100% offline con patrones realistas de churn.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generar_dataset_club_carrefour(n_clientes: int = 2500, seed: int = 42) -> pd.DataFrame:
    """Genera un DataFrame etiquetado de riesgo de abandono (churn) en Club Carrefour."""
    rng = np.random.default_rng(seed)

    visitas_mes = rng.poisson(lam=4.2, size=n_clientes).clip(0, 20)
    ticket_medio = rng.normal(loc=54.0, scale=22.0, size=n_clientes).clip(8.0, 220.0).round(2)
    dias_ultima_compra = rng.exponential(scale=18.0, size=n_clientes).clip(1, 120).round().astype(int)
    cheque_ahorro = (visitas_mes * ticket_medio * 0.015 + rng.normal(2.0, 3.0, n_clientes)).clip(0.0, 80.0).round(2)
    usa_app = rng.binomial(1, 0.58, size=n_clientes)
    compra_drive = rng.binomial(1, 0.28, size=n_clientes)
    quejas_90d = rng.poisson(lam=0.35, size=n_clientes).clip(0, 5)
    antiguedad_meses = rng.integers(1, 96, size=n_clientes)

    # Relación no lineal realista (~25% tasa de abandono): más días sin comprar + quejas + sin app -> mayor churn
    logit = (
        1.15
        + 0.075 * (dias_ultima_compra - 18)
        - 0.30 * visitas_mes
        - 0.012 * (ticket_medio - 50)
        + 1.05 * quejas_90d
        - 0.90 * usa_app
        - 0.70 * compra_drive
        - 0.012 * antiguedad_meses
        + 0.70 * ((dias_ultima_compra > 28) & (usa_app == 0)).astype(float)
        + rng.normal(0.0, 0.55, size=n_clientes)
    )
    prob_churn = 1.0 / (1.0 + np.exp(-logit))
    abandono = (prob_churn > 0.50).astype(int)

    return pd.DataFrame(
        {
            "visitas_ultimo_mes": visitas_mes.astype(float),
            "ticket_medio_eur": ticket_medio.astype(float),
            "dias_desde_ultima_compra": dias_ultima_compra.astype(float),
            "cheque_ahorro_eur": cheque_ahorro.astype(float),
            "usa_app_mi_carrefour": usa_app.astype(float),
            "compra_online_drive": compra_drive.astype(float),
            "quejas_90d": quejas_90d.astype(float),
            "antiguedad_meses": antiguedad_meses.astype(float),
            "abandono": abandono,
        }
    )


if __name__ == "__main__":
    df = generar_dataset_club_carrefour()
    print(f"Dataset generado: {df.shape} | Tasa de abandono: {df['abandono'].mean():.1%}")
    print(df.head(5).to_string(index=False))
