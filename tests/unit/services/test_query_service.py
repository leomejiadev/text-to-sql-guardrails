import pytest
from unittest.mock import MagicMock
from app.services.query_service import QueryService, QueryBlockedError
from app.schemas.sql_output import SQLOutput
from app.schemas.sql_result import SQLResult


def _make_output(sql: str = "SELECT * FROM orders") -> SQLOutput:
    return SQLOutput(
        sql=sql,
        confidence="high",
        tables_used=["orders"],
        detected_language="en",
        response_hint="Devuelve todas las órdenes",
    )


@pytest.fixture
def deps():
    embedding_service = MagicMock()
    schema_repository = MagicMock()
    schema_repository.find_relevant_tables.return_value = [{"table_name": "orders", "schema_text": "Tabla orders..."}]
    schema_repository.get_valid_sql_tables.return_value = {"orders"}
    query_repository = MagicMock()
    query_repository.execute_sql.return_value = [{"id": 1, "total": 100}]
    chain = MagicMock()
    chain.run.return_value = _make_output()
    session = MagicMock()
    # Redis debe mockearse: sin esto QueryService intenta conectar a Redis real
    # en tests unitarios, lo cual rompe el aislamiento y falla en CI sin Redis.
    mock_redis = MagicMock()
    mock_redis.get.return_value = None  # cache miss forzado
    return embedding_service, schema_repository, query_repository, chain, session, mock_redis


def test_full_pipeline_returns_sql_result(deps):
    """process() devuelve SQLResult con sql + results ejecutados contra el cliente."""
    emb, schema_repo, query_repo, chain, session, mock_redis = deps
    service = QueryService(emb, schema_repo, query_repo, chain, session)
    service._redis = mock_redis

    result = service.process("show all orders", "user_1")

    assert isinstance(result, SQLResult)
    assert result.sql == "SELECT * FROM orders"
    assert result.results == [{"id": 1, "total": 100}]
    assert result.row_count == 1


def test_full_pipeline_calls_execute_sql(deps):
    """Verifica que se llama execute_sql con el SQL generado."""
    emb, schema_repo, query_repo, chain, session, mock_redis = deps
    service = QueryService(emb, schema_repo, query_repo, chain, session)
    service._redis = mock_redis

    service.process("show all orders", "user_1")

    query_repo.execute_sql.assert_called_once_with("SELECT * FROM orders")


def test_blocked_guardrail_raises_query_blocked_error(deps):
    emb, schema_repo, query_repo, chain, session, mock_redis = deps
    chain.run.return_value = _make_output(sql="DROP TABLE orders")
    service = QueryService(emb, schema_repo, query_repo, chain, session)
    service._redis = mock_redis
    with pytest.raises(QueryBlockedError):
        service.process("drop orders table", "user_1")


def test_blocked_query_does_not_call_execute_sql(deps):
    """SQL bloqueado nunca llega a ejecutarse contra la DB del cliente."""
    emb, schema_repo, query_repo, chain, session, mock_redis = deps
    chain.run.return_value = _make_output(sql="DROP TABLE orders")
    service = QueryService(emb, schema_repo, query_repo, chain, session)
    service._redis = mock_redis
    with pytest.raises(QueryBlockedError):
        service.process("drop orders table", "user_1")
    query_repo.execute_sql.assert_not_called()


def test_history_saved_with_was_blocked_true(deps):
    emb, schema_repo, query_repo, chain, session, mock_redis = deps
    chain.run.return_value = _make_output(sql="DROP TABLE orders")
    service = QueryService(emb, schema_repo, query_repo, chain, session)
    service._redis = mock_redis
    with pytest.raises(QueryBlockedError):
        service.process("drop orders table", "user_1")
    session.add.assert_called_once()
    history = session.add.call_args[0][0]
    assert history.was_blocked is True


def test_history_saved_with_executed_true(deps):
    emb, schema_repo, query_repo, chain, session, mock_redis = deps
    service = QueryService(emb, schema_repo, query_repo, chain, session)
    service._redis = mock_redis
    service.process("show all orders", "user_1")
    session.add.assert_called_once()
    history = session.add.call_args[0][0]
    assert history.executed is True
