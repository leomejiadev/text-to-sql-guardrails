"""Tests de integración del pipeline completo.

LLM mockeado, guardrails reales, DB real para persistir QueryHistory.
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from app.schemas.sql_output import SQLOutput
from app.services.query_service import QueryService, QueryBlockedError
from app.models.query_history import QueryHistory  # registra el modelo en metadata


@pytest.fixture(scope="module", autouse=True)
def create_query_history_table(test_engine):
    """Crea la tabla query_history solo para este módulo de tests."""
    QueryHistory.__table__.create(test_engine, checkfirst=True)
    yield
    QueryHistory.__table__.drop(test_engine, checkfirst=True)


@pytest.fixture
def history_session(test_engine):
    with Session(test_engine) as session:
        yield session
        session.rollback()


def _make_output(sql: str = "SELECT * FROM orders") -> SQLOutput:
    return SQLOutput(
        sql=sql,
        confidence="high",
        tables_used=["orders"],
        detected_language="es",
        response_hint="Devuelve todas las órdenes",
    )


def _build_service(chain, session) -> QueryService:
    embedding_service = MagicMock()
    schema_repository = MagicMock()
    schema_repository.find_relevant_tables.return_value = [{"table_name": "orders", "schema_text": "Tabla orders..."}]
    schema_repository.get_valid_sql_tables.return_value = {"orders"}
    query_repository = MagicMock()
    query_repository.execute_sql.return_value = [{"id": 1}]
    return QueryService(embedding_service, schema_repository, query_repository, chain, session)


@pytest.mark.integration
def test_pipeline_end_to_end_with_mocked_llm(history_session):
    chain = MagicMock()
    chain.run.return_value = _make_output()
    service = _build_service(chain, history_session)
    results = service.process("show all orders", "user_1")
    assert results.row_count == 1


@pytest.mark.integration
def test_destructive_query_blocked_before_query_repository(history_session):
    chain = MagicMock()
    chain.run.return_value = _make_output(sql="DROP TABLE orders")
    embedding_service = MagicMock()
    schema_repository = MagicMock()
    schema_repository.find_relevant_tables.return_value = [{"table_name": "orders", "schema_text": "Tabla orders..."}]
    query_repository = MagicMock()
    service = QueryService(
        embedding_service, schema_repository, query_repository, chain, history_session
    )
    with pytest.raises(QueryBlockedError):
        service.process("drop orders table", "user_1")
    # El SQL destructivo nunca llegó al QueryRepository
    query_repository.execute_sql.assert_not_called()
