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


def test_find_relevant_tables_returns_list_of_dicts():
    """Verifica que find_relevant_tables() retorna list[dict] con keys table_name y schema_text."""
    mock_session = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [0.1] * 1536

    mock_row1, mock_row2 = MagicMock(), MagicMock()
    mock_row1.table_name = "users"
    mock_row1.schema_text = "CREATE TABLE users (id UUID PRIMARY KEY)"
    mock_row2.table_name = "orders"
    mock_row2.schema_text = "CREATE TABLE orders (id UUID PRIMARY KEY)"
    mock_session.execute.return_value = [mock_row1, mock_row2]

    repo = _make_repo(mock_session=mock_session, mock_embedding_service=mock_embedding)
    result = repo.find_relevant_tables("find all users")

    assert isinstance(result, list)
    assert all(isinstance(t, dict) for t in result)
    assert result[0] == {"table_name": "users", "schema_text": "CREATE TABLE users (id UUID PRIMARY KEY)"}
    assert result[1] == {"table_name": "orders", "schema_text": "CREATE TABLE orders (id UUID PRIMARY KEY)"}


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


def test_index_document_executes_upsert_with_document_type():
    """Verifica que index_document() incluye document_type en el INSERT."""
    mock_session = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.embed.return_value = [0.1] * 3072

    repo = _make_repo(mock_session=mock_session, mock_embedding_service=mock_embedding)
    repo.index_document(doc_type="fewshot", name="fewshot_ventas_mes", text_content="SELECT ...")

    mock_embedding.embed.assert_called_once_with("SELECT ...")
    call_params = mock_session.execute.call_args[0][1]
    assert call_params["doc_type"] == "fewshot"
    assert call_params["table_name"] == "fewshot_ventas_mes"
    mock_session.commit.assert_called_once()


def test_find_relevant_tables_limit_is_six():
    """Verifica que find_relevant_tables() usa LIMIT 6 en la query SQL."""
    from app.repositories.schema_repository import SchemaRepository

    import inspect
    source = inspect.getsource(SchemaRepository.find_relevant_tables)
    assert "LIMIT 6" in source


def test_get_valid_sql_tables_returns_names_without_prefix():
    """Verifica que get_valid_sql_tables() retorna nombres de tabla SQL sin prefijo 'schema_'."""
    mock_session = MagicMock()
    mock_row1, mock_row2 = MagicMock(), MagicMock()
    mock_row1.sql_table = "customers"
    mock_row2.sql_table = "orders"
    mock_session.execute.return_value = [mock_row1, mock_row2]

    repo = _make_repo(mock_session=mock_session)
    result = repo.get_valid_sql_tables()

    assert result == {"customers", "orders"}


def test_get_valid_sql_tables_filters_by_schema_document_type():
    """Verifica que la query filtra WHERE document_type = 'schema'."""
    from app.repositories.schema_repository import SchemaRepository

    import inspect
    source = inspect.getsource(SchemaRepository.get_valid_sql_tables)
    assert "document_type = 'schema'" in source
