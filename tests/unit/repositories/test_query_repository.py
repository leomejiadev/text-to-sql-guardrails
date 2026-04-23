"""Tests unitarios para QueryRepository — DB mockeada."""
import pytest
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


def test_execute_sql_raises_runtime_error_on_failure():
    """Verifica que execute_sql() lanza RuntimeError si la DB lanza excepción."""
    mock_engine = MagicMock()
    mock_conn = mock_engine.connect.return_value.__enter__.return_value
    mock_conn.execute.side_effect = Exception("connection refused")

    repo = _make_repo(mock_engine=mock_engine)
    with pytest.raises(RuntimeError):
        repo.execute_sql("SELECT 1")
