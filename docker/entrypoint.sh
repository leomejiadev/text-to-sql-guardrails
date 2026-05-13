#!/bin/sh
set -e

export PYTHONPATH=/app

echo "→ [1/3] Verificando entorno y conectividad..."
uv run python scripts/pre_deploy_check.py

echo "→ [2/3] Ejecutando migraciones Alembic..."
uv run alembic upgrade head

echo "→ [3/3] Iniciando API..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
