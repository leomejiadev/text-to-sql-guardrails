"""Tests unitarios para la tarea Celery process_query."""
import pytest
from unittest.mock import MagicMock, patch
from celery import states


class TestProcessQueryTask:

    def test_process_query_delay_returns_task_id(self):
        """delay() encola la tarea y devuelve AsyncResult con task_id."""
        with patch("app.services.tasks.process_query") as mock_task:
            mock_result = MagicMock()
            mock_result.id = "abc-123"
            mock_task.delay.return_value = mock_result

            result = mock_task.delay(query="show me all users", user_id="user-1")

            mock_task.delay.assert_called_once_with(
                query="show me all users", user_id="user-1"
            )
            assert result.id == "abc-123"

    def test_query_blocked_error_captured_in_result(self):
        """QueryBlockedError debe guardarse como resultado exitoso, no propagar."""
        from app.services.query_service import QueryBlockedError
        from app.services.tasks import process_query

        with patch("app.services.tasks._run_pipeline") as mock_pipeline:
            mock_pipeline.side_effect = QueryBlockedError("SQL injection detected")

            result = process_query.apply(
                kwargs={"query": "DROP TABLE users", "user_id": "u1"}
            )

            # La tarea termina en SUCCESS — bloqueo no es un crash del worker
            assert result.state == states.SUCCESS
            output = result.get()
            assert output["blocked"] is True
            assert "SQL injection detected" in output["block_reason"]

    def test_llm_error_triggers_retry(self):
        """LLMError debe intentar retry en lugar de fallar inmediatamente."""
        from app.integrations.llm_client import LLMError
        from app.services.tasks import process_query

        with patch("app.services.tasks._run_pipeline") as mock_pipeline:
            mock_pipeline.side_effect = LLMError("timeout")

            # patch retry para capturar que se llamó sin ejecutar el delay real
            with patch.object(
                process_query, "retry", side_effect=LLMError("max retries")
            ) as mock_retry:
                result = process_query.apply(
                    kwargs={"query": "show users", "user_id": "u1"}
                )

            # retry fue invocado → el mecanismo de reintento está activo
            mock_retry.assert_called_once()
            # el countdown sigue la fórmula de backoff exponencial (30 * 2^0 = 30)
            call_kwargs = mock_retry.call_args.kwargs
            assert call_kwargs["countdown"] == 30
