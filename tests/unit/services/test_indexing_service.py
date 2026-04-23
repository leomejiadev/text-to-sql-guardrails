"""Tests unitarios para IndexingService — repositories mockeados."""
from unittest.mock import MagicMock


def _make_service(query_repo=None, schema_repo=None):
    """Construye IndexingService con repositories mockeados."""
    from app.services.indexing_service import IndexingService

    return IndexingService(
        query_repository=query_repo or MagicMock(),
        schema_repository=schema_repo or MagicMock(),
    )


def test_reindex_calls_get_schema():
    """Verifica que reindex() llama a get_schema() exactamente una vez."""
    mock_query_repo = MagicMock()
    mock_query_repo.get_schema.return_value = {}
    mock_schema_repo = MagicMock()

    service = _make_service(query_repo=mock_query_repo, schema_repo=mock_schema_repo)
    service.reindex()

    mock_query_repo.get_schema.assert_called_once()


def test_reindex_calls_reindex_all_with_schema():
    """Verifica que reindex() pasa la salida de get_schema() a reindex_all()."""
    schemas = {"users": "Tabla users, columnas: id uuid, name varchar"}
    mock_query_repo = MagicMock()
    mock_query_repo.get_schema.return_value = schemas
    mock_schema_repo = MagicMock()

    service = _make_service(query_repo=mock_query_repo, schema_repo=mock_schema_repo)
    service.reindex()

    mock_schema_repo.reindex_all.assert_called_once_with(schemas)


def test_reindex_returns_correct_structure():
    """Verifica que reindex() retorna dict con 'reindexed_tables' y 'status'."""
    mock_query_repo = MagicMock()
    mock_query_repo.get_schema.return_value = {"a": "...", "b": "...", "c": "..."}
    mock_schema_repo = MagicMock()

    service = _make_service(query_repo=mock_query_repo, schema_repo=mock_schema_repo)
    result = service.reindex()

    assert "reindexed_tables" in result
    assert "status" in result
    assert result["reindexed_tables"] == 3
    assert result["status"] == "success"
