"""Tests unitarios para QueryRepository — DB mockeada."""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock


def _make_repo(mock_engine=None):
    """Construye QueryRepository con engine mockeado."""
    from app.repositories.query_repository import QueryRepository

    return QueryRepository(engine=mock_engine or MagicMock())


def test_execute_sql_returns_list_of_dicts():
    """Verifica que execute_sql() retorna list[dict]."""
    mock_engine = MagicMock()
    mock_conn = mock_engine.connect.return_value.__enter__.return_value

    mock_row = MagicMock()
    mock_row._mapping = {"id": 1, "name": "Alice"}
    mock_conn.execute.return_value = [mock_row]

    repo = _make_repo(mock_engine=mock_engine)
    result = repo.execute_sql("SELECT id, name FROM users")

    assert isinstance(result, list)
    assert all(isinstance(row, dict) for row in result)


def test_execute_sql_converts_decimal_to_float():
    """Verifica que valores Decimal de PostgreSQL se convierten a float."""
    mock_engine = MagicMock()
    mock_conn = mock_engine.connect.return_value.__enter__.return_value

    mock_row = MagicMock()
    mock_row._mapping = {"total": Decimal("123.45"), "id": 1}
    mock_conn.execute.return_value = [mock_row]

    repo = _make_repo(mock_engine=mock_engine)
    result = repo.execute_sql("SELECT id, total FROM orders")

    assert result[0]["total"] == 123.45
    assert isinstance(result[0]["total"], float)
    assert result[0]["id"] == 1


def test_execute_sql_raises_runtime_error_on_failure():
    """Verifica que execute_sql() lanza RuntimeError si la DB lanza excepción."""
    mock_engine = MagicMock()
    mock_conn = mock_engine.connect.return_value.__enter__.return_value
    mock_conn.execute.side_effect = Exception("connection refused")

    repo = _make_repo(mock_engine=mock_engine)
    with pytest.raises(RuntimeError):
        repo.execute_sql("SELECT 1")
