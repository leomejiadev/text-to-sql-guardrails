"""Tests end-to-end: ejercen el stack completo via HTTP con worker Celery real.

Estrategia para evitar llamadas reales al LLM con worker en proceso separado:
pre-poblamos el cache Redis con un SQLOutput conocido. El worker hace cache hit
y devuelve el resultado sin necesidad de GEMINI_API_KEY en el entorno de test.
"""
import hashlib
import time

import pytest
from unittest.mock import patch

from app.schemas.sql_output import SQLOutput

POLL_INTERVAL = 0.5   # segundos entre cada poll
POLL_TIMEOUT = 30     # máximo de espera por tarea


def _poll_result(app_client, task_id: str, timeout: int = POLL_TIMEOUT) -> dict:
    """Hace polling a GET /query/{task_id} hasta que la tarea esté lista."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = app_client.get(f"/api/v1/query/{task_id}")
        if response.status_code == 200:
            return response.json()
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"tarea {task_id} no completó en {timeout}s — ¿worker corriendo?")


def _seed_cache(redis_client, query: str, sql_output: SQLOutput) -> str:
    """Pre-popula Redis con el output esperado para evitar llamada real al LLM.

    Usa la misma cache_key que QueryService para que el worker haga hit.
    """
    cache_key = hashlib.md5(query.strip().lower().encode()).hexdigest()
    redis_client.setex(cache_key, 3600, sql_output.model_dump_json())
    return cache_key


@pytest.fixture
def known_output() -> SQLOutput:
    """SQLOutput fijo reutilizado en múltiples tests."""
    return SQLOutput(
        sql="SELECT id, name FROM employees",
        confidence="high",
        tables_used=["employees"],
        detected_language="en",
        response_hint="Returns all employees",
    )


def test_pipeline_enqueues_processes_and_result_available(app_client, redis_client, known_output):
    """Pipeline completo: POST encola, worker procesa, GET devuelve resultado."""
    query = "list all users e2e pipeline test"
    _seed_cache(redis_client, query, known_output)

    post_response = app_client.post(
        "/api/v1/query", json={"query": query, "user_id": "test_user"}
    )
    assert post_response.status_code == 202
    task_id = post_response.json()["task_id"]
    assert task_id  # task_id no puede estar vacío

    result = _poll_result(app_client, task_id)
    assert result["sql"] == "SELECT id, name FROM employees"


def test_cache_hit_second_identical_query_skips_llm(app_client, redis_client, known_output):
    """Segunda query idéntica debe tener cache hit: el resultado es el mismo sin llamar al LLM."""
    query = "list all users e2e cache hit test"
    cache_key = _seed_cache(redis_client, query, known_output)

    # Primera query: worker procesa y usa cache pre-poblado
    r1 = app_client.post("/api/v1/query", json={"query": query, "user_id": "user_a"})
    result_1 = _poll_result(app_client, r1.json()["task_id"])

    # El cache debe seguir vivo para la segunda query
    assert redis_client.exists(cache_key), "cache borrado inesperadamente entre queries"

    # Segunda query idéntica: worker hace cache hit inmediato
    r2 = app_client.post("/api/v1/query", json={"query": query, "user_id": "user_b"})
    result_2 = _poll_result(app_client, r2.json()["task_id"])

    # Mismo SQL en ambas respuestas confirma que vino del cache
    assert result_1["sql"] == result_2["sql"] == "SELECT id, name FROM employees"


def test_reindex_manual_indexes_tables_and_returns_count(app_client):
    """POST /admin/reindex-schema indexa tablas en pgvector y devuelve tables_indexed."""
    # IndexingService es síncrono en el proceso HTTP (no Celery), por eso
    # se puede mockear con patch aquí — no afecta al worker.
    with patch("app.api.admin_router.IndexingService") as mock_svc:
        mock_svc.return_value.reindex.return_value = 3

        response = app_client.post("/api/v1/admin/reindex-schema")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "reindex completed"
    assert body["tables_indexed"] == 3
