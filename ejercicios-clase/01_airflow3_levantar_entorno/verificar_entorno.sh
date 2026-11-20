#!/usr/bin/env bash
set -euo pipefail

echo "=== 1. Comprobando PostgreSQL (carrefour_dw) ==="
docker exec clase-carrefour-postgres psql -U airflow -d carrefour_dw -c \
  "SELECT tienda_id, nombre, formato, provincia FROM silver.dim_tiendas ORDER BY tienda_id;"

echo ""
echo "=== 2. Comprobando salud del API Server de Airflow 3 ==="
curl -sf http://localhost:8080/api/v2/monitor/health && echo ""

echo ""
echo "=== 3. Listando DAGs detectados ==="
docker exec clase-carrefour-airflow3 airflow dags list

echo ""
echo "Todo listo. Abre la UI React de Airflow 3 en: http://localhost:8080"
