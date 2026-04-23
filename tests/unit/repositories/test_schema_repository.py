"""Tests unitarios para SchemaRepository — EmbeddingService mockeado."""
from unittest.mock import MagicMock, patch


def _make_repo(mock_session=None, mock_embedding_service=None):
    """Construye SchemaRepository con dependencias mockeadas."""
    from app.repositories.schema_repository import SchemaRepository

    session = mock_session or MagicMock()
    embedding_service = mock_embedding_service or MagicMock()
    return SchemaRepository(session=session, embedding_service=embedding_service)


def test_index_schema_calls_embedding_service():
    """Verifica que index_schema() llama a embed() con el schema_text correcto."""
    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [0.1] * 1536

    repo = _make_repo(mock_embedding_service=mock_embedding)
    repo.index_schema("users", "CREATE TABLE users (id UUID PRIMARY KEY)")

    mock_embedding.embed.assert_called_once_with("CREATE TABLE users (id UUID PRIMARY KEY)")


def test_find_relevant_tables_returns_list_of_strings():
    """Verifica que find_relevant_tables() retorna list[str]."""
    mock_session = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [0.1] * 1536

    # Simular filas con atributo table_name
    mock_row1, mock_row2 = MagicMock(), MagicMock()
    mock_row1.table_name = "users"
    mock_row2.table_name = "orders"
    mock_session.execute.return_value = [mock_row1, mock_row2]

    repo = _make_repo(mock_session=mock_session, mock_embedding_service=mock_embedding)
    result = repo.find_relevant_tables("find all users")

    assert isinstance(result, list)
    assert all(isinstance(t, str) for t in result)


def test_reindex_all_calls_index_schema_for_each_table():
    """Verifica que reindex_all() llama index_schema() exactamente una vez por tabla."""
    schemas = {
        "users": "CREATE TABLE users ...",
        "orders": "CREATE TABLE orders ...",
        "products": "CREATE TABLE products ...",
    }

    repo = _make_repo()
    with patch.object(repo, "index_schema") as mock_index:
        repo.reindex_all(schemas)
        assert mock_index.call_count == 3
