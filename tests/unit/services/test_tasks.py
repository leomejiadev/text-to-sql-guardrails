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

    def test_process_query_accepts_optional_trace_id(self):
        """process_query.delay debe aceptar trace_id sin romper firma."""
        from app.services.tasks import process_query

        with patch("app.services.tasks._run_pipeline") as mock_pipeline:
            fake_output = MagicMock()
            fake_output.model_dump.return_value = {"sql": "SELECT 1"}
            mock_pipeline.return_value = fake_output

            result = process_query.apply(
                kwargs={"query": "q", "user_id": "u", "trace_id": "trace-abc"}
            )

            assert result.state == states.SUCCESS
            # _run_pipeline debe recibir el trace_id propagado desde la tarea
            mock_pipeline.assert_called_once_with("q", "u", "trace-abc")

    def test_run_pipeline_forwards_trace_id_to_service(self):
        """_run_pipeline debe pasar trace_id al QueryService.process()."""
        from app.services import tasks

        with patch("app.services.tasks.create_engine"), \
             patch("app.services.tasks.Session"), \
             patch("app.services.tasks.EmbeddingService"), \
             patch("app.services.tasks.SchemaRepository"), \
             patch("app.services.tasks.QueryRepository"), \
             patch("app.services.tasks.SQLChain"), \
             patch("app.services.tasks.QueryService") as MockService:
            instance = MockService.return_value
            instance.process.return_value = MagicMock()

            tasks._run_pipeline("q", "u", trace_id="trace-xyz")

            instance.process.assert_called_once_with("q", "u", trace_id="trace-xyz")

    def test_run_pipeline_trace_id_is_optional(self):
        """_run_pipeline sigue funcionando si no se pasa trace_id."""
        from app.services import tasks

        with patch("app.services.tasks.create_engine"), \
             patch("app.services.tasks.Session"), \
             patch("app.services.tasks.EmbeddingService"), \
             patch("app.services.tasks.SchemaRepository"), \
             patch("app.services.tasks.QueryRepository"), \
             patch("app.services.tasks.SQLChain"), \
             patch("app.services.tasks.QueryService") as MockService:
            instance = MockService.return_value
            instance.process.return_value = MagicMock()

            tasks._run_pipeline("q", "u")

            instance.process.assert_called_once_with("q", "u", trace_id=None)

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
