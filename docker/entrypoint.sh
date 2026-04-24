#!/bin/sh
set -e

# Asegura que los módulos del proyecto sean encontrables desde cualquier script
export PYTHONPATH=/app

echo "→ [1/5] Verificando entorno y conectividad..."
uv run python scripts/pre_deploy_check.py

echo "→ [2/5] Ejecutando migraciones Alembic..."
uv run alembic upgrade head

echo "→ [3/5] Seeding DB del cliente (si está vacía)..."
uv run python scripts/seed_client_db.py

echo "→ [4/5] Reindexando schemas + knowledge base..."
uv run python scripts/reindex_all.py

echo "→ [5/5] Iniciando API..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
