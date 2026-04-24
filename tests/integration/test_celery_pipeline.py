"""Tests de integración: Celery worker + Redis + cache.

Requieren Redis y Postgres corriendo. Correr con:
    pytest tests/integration/test_celery_pipeline.py -m integration -v

Estrategia: pre-poblar Redis cache antes de despachar la tarea.
El worker lee el cache y no llama al LLM — los tests verifican
infraestructura (broker, backend, serialización, red Docker), no lógica de negocio.
"""
import hashlib
import os

import pytest
import redis

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def celery_worker_available():
    """Verifica que el worker Celery pueda procesar tareas enviando un ping real."""
    from app.services.tasks import celery_app

    # ping() envía un mensaje y espera respuesta — garantiza que el worker
    # puede recibir y procesar tareas, no solo que está conectado a Redis
    responses = celery_app.control.ping(timeout=3)
    if not responses:
        pytest.skip("Celery worker no disponible — saltando test de integración")


@pytest.fixture(scope="module")
def redis_client():
    return redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))


class TestCeleryPipeline:

    def test_task_result_serializes_through_redis(self, celery_worker_available, redis_client):
        """Verifica serialización completa: broker → worker → Redis backend → proceso de test."""
        from app.schemas.sql_output import SQLOutput
        from app.services import tasks

        query = "infrastructure serialization test celery broker"
        cache_key = hashlib.md5(query.strip().lower().encode()).hexdigest()

        # Pre-poblar cache: el worker lee esto y ejecuta el SQL sin llamar al LLM
        # SELECT 1 es válido en cualquier PostgreSQL — no depende de tablas del cliente
        sql_out = SQLOutput(
            sql="SELECT 1 AS result",
            detected_language="en",
            confidence="high",
            tables_used=["schema_embeddings"],
            response_hint="test de infraestructura",
        )
        redis_client.setex(cache_key, 60, sql_out.model_dump_json())

        try:
            async_result = tasks.process_query.delay(query=query, user_id="integration-user")
            result = async_result.get(timeout=15)
        finally:
            redis_client.delete(cache_key)

        assert isinstance(result, dict)
        assert result["sql"] == "SELECT 1 AS result"
        assert result["row_count"] == 1

    def test_cache_hit_avoids_llm_on_second_identical_query(self, celery_worker_available, redis_client):
        """Worker lee del cache Redis: devuelve el SQL cacheado, no una respuesta del LLM."""
        from app.schemas.sql_output import SQLOutput
        from app.services import tasks

        query = "unique sentinel query for cache hit test xyz789"
        cache_key = hashlib.md5(query.strip().lower().encode()).hexdigest()

        # SQL sentinel imposible de generar orgánicamente por el LLM:
        # si el resultado contiene este valor, el worker leyó del cache
        sentinel_sql = "SELECT 'cache_hit_sentinel_abc123' AS proof"
        sql_out = SQLOutput(
            sql=sentinel_sql,
            detected_language="en",
            confidence="high",
            tables_used=["users"],
            response_hint="prueba de cache hit",
        )
        redis_client.setex(cache_key, 60, sql_out.model_dump_json())

        try:
            result = tasks.process_query.delay(query=query, user_id="u1").get(timeout=15)
        finally:
            redis_client.delete(cache_key)

        assert result["sql"] == sentinel_sql
