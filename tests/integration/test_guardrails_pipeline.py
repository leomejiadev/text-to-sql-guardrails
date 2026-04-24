"""Tests de integración para el pipeline de guardrails.

Verifican que las queries destructivas son bloqueadas ANTES de llegar
a QueryRepository, usando LLM mockeado que devuelve el SQL indicado.
Estos tests deben pasar siempre — son la red de seguridad del sistema.
"""
import pytest
from unittest.mock import MagicMock

from app.schemas.sql_output import SQLOutput
from app.services.query_service import QueryService, QueryBlockedError


def _make_service(mock_sql: str) -> tuple[QueryService, MagicMock]:
    """Construye un QueryService con LLM mockeado que devuelve `mock_sql`."""
    mock_chain = MagicMock()
    mock_chain.run.return_value = SQLOutput(
        sql=mock_sql,
        confidence="high",
        tables_used=["users"],
        detected_language="en",
        response_hint="test hint",
    )
    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [0.1] * 3072

    mock_schema_repo = MagicMock()
    mock_schema_repo.find_relevant_tables.return_value = [{"table_name": "users", "schema_text": "Tabla users..."}]

    mock_query_repo = MagicMock()
    mock_session = MagicMock()
    mock_redis = MagicMock()
    # Cache miss forzado: el pipeline siempre llega hasta los guardrails
    mock_redis.get.return_value = None

    service = QueryService(
        embedding_service=mock_embedding,
        schema_repository=mock_schema_repo,
        query_repository=mock_query_repo,
        chain=mock_chain,
        session=mock_session,
    )
    # Inyección directa para evitar conexión Redis real en tests de guardrails
    service._redis = mock_redis
    return service, mock_query_repo


def test_drop_table_is_blocked_before_repository():
    """DROP TABLE debe ser bloqueado por guardrails; QueryRepository.execute() nunca se llama."""
    service, mock_query_repo = _make_service("DROP TABLE users")

    with pytest.raises(QueryBlockedError):
        service.process("drop users table", "user1")

    # El guardrail corta el pipeline antes de llegar al repositorio
    mock_query_repo.execute.assert_not_called()


def test_delete_from_is_blocked_with_reason():
    """DELETE FROM debe levantar QueryBlockedError con block_reason no vacío."""
    service, _ = _make_service("DELETE FROM users WHERE id = 1")

    with pytest.raises(QueryBlockedError) as exc_info:
        service.process("delete user 1", "user1")

    assert exc_info.value.reason


def test_update_is_blocked_with_reason():
    """UPDATE debe levantar QueryBlockedError con block_reason no vacío."""
    service, _ = _make_service("UPDATE users SET name = 'x' WHERE id = 1")

    with pytest.raises(QueryBlockedError) as exc_info:
        service.process("change user name", "user1")

    assert exc_info.value.reason


def test_truncate_is_blocked_with_reason():
    """TRUNCATE debe levantar QueryBlockedError con block_reason no vacío."""
    service, _ = _make_service("TRUNCATE TABLE users")

    with pytest.raises(QueryBlockedError) as exc_info:
        service.process("truncate users", "user1")

    assert exc_info.value.reason


def test_clean_select_passes_guardrails():
    """Un SELECT limpio no debe ser bloqueado y debe completar el pipeline."""
    service, _ = _make_service("SELECT id, name FROM users")

    result = service.process("list all users", "user1")

    assert result.sql == "SELECT id, name FROM users"
    # Si llegamos aquí sin excepción, los guardrails no bloquearon
