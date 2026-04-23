"""Tests de integración: Celery worker + Redis + cache.

Requieren Redis y Postgres corriendo. Correr con:
    pytest tests/integration/test_celery_pipeline.py -m integration -v
"""
import hashlib
import os

import pytest
import redis

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def celery_worker_available():
    """Verifica que el worker Celery esté accesible vía Redis."""
    from app.services.tasks import celery_app

    inspector = celery_app.control.inspect(timeout=3)
    active = inspector.active()
    if not active:
        pytest.skip("Celery worker no disponible — saltando test de integración")


class TestCeleryPipeline:

    def test_task_result_available_in_redis(self, celery_worker_available):
        """La tarea llega al worker y el resultado queda disponible en Redis."""
        from unittest.mock import patch
        from app.schemas.sql_output import SQLOutput
        from app.services import tasks

        sql_out = SQLOutput(
            sql="SELECT * FROM users",
            detected_language="en",
            confidence="high",
            tables_used=["users"],
            response_hint="todos los usuarios",
        )

        with patch("app.services.tasks._run_pipeline", return_value=sql_out):
            async_result = tasks.process_query.delay(
                query="show all users", user_id="integration-user"
            )
            result = async_result.get(timeout=10)

        assert result["sql"] == "SELECT * FROM users"

    def test_cache_hit_avoids_llm_on_second_identical_query(self, celery_worker_available):
        """Segunda query idéntica usa cache Redis y no llama al LLM."""
        from unittest.mock import patch
        from app.schemas.sql_output import SQLOutput
        from app.services import tasks

        query = "unique integration test query 12345"
        cache_key = hashlib.md5(query.strip().lower().encode()).hexdigest()

        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.delete(cache_key)

        sql_out = SQLOutput(
            sql="SELECT id FROM users",
            detected_language="en",
            confidence="high",
            tables_used=["users"],
            response_hint="IDs de usuarios",
        )

        def fake_pipeline(q, user_id):
            # Simula primera ejecución real: guarda en cache y retorna
            r.setex(cache_key, 3600, sql_out.model_dump_json())
            return sql_out

        with patch("app.services.tasks._run_pipeline", side_effect=fake_pipeline):
            tasks.process_query.delay(query=query, user_id="u1").get(timeout=10)

        # Segunda llamada — cache hit, _run_pipeline no debe ser invocado
        with patch("app.services.tasks._run_pipeline") as mock_pipeline:
            mock_pipeline.return_value = sql_out
            tasks.process_query.delay(query=query, user_id="u2").get(timeout=10)

        mock_pipeline.assert_not_called()

        r.delete(cache_key)
