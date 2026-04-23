"""
Tests de integración — requieren PostgreSQL + pgvector corriendo.
Verifican que el pipeline completo de indexing funciona de punta a punta.
Usan una DB de test separada configurada en TEST_DATABASE_URL.
"""
import pytest
from sqlalchemy import text


@pytest.mark.integration
def test_index_schema_persists_in_pgvector(db_session, embedding_service):
    """Verifica que index_schema() persiste el registro en schema_embeddings."""
    from app.repositories.schema_repository import SchemaRepository

    repo = SchemaRepository(session=db_session, embedding_service=embedding_service)
    repo.index_schema(
        "integration_test_table",
        "Tabla integration_test_table con columnas: id uuid, nombre varchar",
    )

    result = db_session.execute(
        text("SELECT table_name FROM schema_embeddings WHERE table_name = :name"),
        {"name": "integration_test_table"},
    ).fetchone()

    assert result is not None
    assert result.table_name == "integration_test_table"


@pytest.mark.integration
def test_find_relevant_tables_returns_semantically_similar_results(db_session, embedding_service):
    """Verifica que find_relevant_tables() devuelve la tabla más relevante semánticamente."""
    from app.repositories.schema_repository import SchemaRepository

    repo = SchemaRepository(session=db_session, embedding_service=embedding_service)

    # Indexar tres schemas con dominios bien diferenciados
    repo.index_schema("clientes", "Tabla clientes: id uuid, nombre varchar, email varchar")
    repo.index_schema("productos", "Tabla productos: id uuid, nombre varchar, precio decimal")
    repo.index_schema("inventario", "Tabla inventario: id uuid, producto_id uuid, stock integer")

    # La query apunta semánticamente a 'clientes'
    result = repo.find_relevant_tables("mostrar todos los usuarios registrados con su correo")

    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0] == "clientes"


@pytest.mark.integration
def test_full_reindex_pipeline(db_session, embedding_service, test_engine):
    """Verifica que IndexingService.reindex() indexa todos los schemas en pgvector."""
    from app.repositories.query_repository import QueryRepository
    from app.repositories.schema_repository import SchemaRepository
    from app.services.indexing_service import IndexingService

    schema_repo = SchemaRepository(session=db_session, embedding_service=embedding_service)
    # Usamos la test DB como "DB del cliente" — tiene al menos schema_embeddings
    query_repo = QueryRepository(engine=test_engine)
    service = IndexingService(query_repository=query_repo, schema_repository=schema_repo)

    result = service.reindex()

    assert result["status"] == "success"
    assert isinstance(result["reindexed_tables"], int)
    assert result["reindexed_tables"] >= 0
