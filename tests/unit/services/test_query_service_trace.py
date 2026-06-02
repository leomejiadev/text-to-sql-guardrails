"""Tests de instrumentación LangSmith en QueryService."""
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.sql_output import SQLOutput
from app.services.query_service import QueryService


def _make_output(sql: str = "SELECT 1") -> SQLOutput:
    return SQLOutput(
        sql=sql,
        confidence="high",
        tables_used=["t"],
        detected_language="es",
        response_hint="ok",
    )


@pytest.fixture
def service_with_mocks():
    """Construye un QueryService con todas las deps mockeadas y cache miss."""
    chain = MagicMock()
    chain.run.return_value = _make_output()
    schema_repo = MagicMock()
    schema_repo.find_relevant_tables.return_value = [
        {"table_name": "t", "schema_text": "Tabla t..."}
    ]
    schema_repo.get_valid_sql_tables.return_value = {"t"}
    query_repo = MagicMock()
    query_repo.execute_sql.return_value = [{"id": 1}]

    svc = QueryService(
        embedding_service=MagicMock(),
        schema_repository=schema_repo,
        query_repository=query_repo,
        chain=chain,
        session=MagicMock(),
    )
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    svc._redis = mock_redis
    return svc, chain


class TestProcessTraceIdSignature:
    def test_process_without_trace_id_is_backward_compatible(self, service_with_mocks):
        # Tests existentes no pasan trace_id; la firma debe seguir funcionando.
        svc, _ = service_with_mocks
        result = svc.process("q", "u")
        assert result.sql == "SELECT 1"

    def test_process_accepts_optional_trace_id(self, service_with_mocks):
        svc, _ = service_with_mocks
        result = svc.process("q", "u", trace_id="abc-123")
        assert result.sql == "SELECT 1"


class TestTraceIdPropagation:
    def test_trace_id_is_forwarded_to_chain_run(self, service_with_mocks):
        # El trace_id que entra en process() debe llegar a SQLChain.run para
        # correlacionar la subcadena LCEL con el run padre query-pipeline.
        svc, chain = service_with_mocks
        svc.process("q", "u", trace_id="trace-xyz")
        chain.run.assert_called_once()
        kwargs = chain.run.call_args.kwargs
        assert kwargs.get("trace_id") == "trace-xyz"

    def test_no_trace_id_means_chain_receives_none(self, service_with_mocks):
        svc, chain = service_with_mocks
        svc.process("q", "u")
        kwargs = chain.run.call_args.kwargs
        assert kwargs.get("trace_id") is None


class TestObservabilityNeverBreaksPipeline:
    def test_pipeline_succeeds_when_langsmith_trace_raises(self, service_with_mocks):
        # Si langsmith.trace explota (API down, key inválida, etc.) el pipeline
        # debe completar y devolver SQLResult — observabilidad es opcional.
        svc, _ = service_with_mocks
        with patch(
            "app.services.query_service.ls_trace",
            side_effect=RuntimeError("langsmith down"),
        ):
            result = svc.process("q", "u", trace_id="abc")
        assert result.sql == "SELECT 1"
        assert result.row_count == 1


class TestObservabilityDecorators:
    def test_process_is_decorated_with_traceable(self):
        # @traceable de langsmith setea __wrapped__ sobre la función decorada.
        # query-pipeline ahora se instrumenta vía @traceable, no vía _traced.
        from app.services.query_service import QueryService

        assert hasattr(QueryService.process, "__wrapped__"), (
            "process() debe estar decorada con @traceable para emitir el run "
            "padre 'query-pipeline'"
        )

    def test_traced_helper_wraps_external_steps(self, service_with_mocks):
        # Los pasos que envuelven llamadas a clases externas (redis,
        # EmbeddingService, SchemaRepository, Guardrails, QueryRepository)
        # siguen pasando por _traced/ls_trace porque @traceable no aplica
        # a métodos de otras capas. query-pipeline NO debe aparecer acá:
        # lo maneja @traceable sobre process(), no ls_trace.
        svc, _ = service_with_mocks
        recorded_names: list[str] = []

        def fake_trace(name, **_kwargs):
            recorded_names.append(name)
            cm = MagicMock()
            cm.__enter__ = MagicMock(return_value=cm)
            cm.__exit__ = MagicMock(return_value=False)
            return cm

        with patch("app.services.query_service.ls_trace", side_effect=fake_trace):
            svc.process("q", "u", trace_id="abc")

        assert "query-pipeline" not in recorded_names
        assert "cache-check" in recorded_names
        assert "embedding" in recorded_names
        assert "rag-retrieval" in recorded_names
        assert "sql-execution" in recorded_names
        # Al menos un guardrail-* fue instrumentado (factory devuelve >=1)
        assert any(n.startswith("guardrail-") for n in recorded_names)
