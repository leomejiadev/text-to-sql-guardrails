from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Importamos aquí para que el patch esté activo antes de crear la app
    from app.main import app
    return TestClient(app)


def test_reindex_schema_returns_200_with_tables_indexed(client):
    with patch("app.api.admin_router.IndexingService") as MockService:
        MockService.return_value.reindex.return_value = {"reindexed_tables": 5, "status": "success"}

        response = client.post("/api/v1/admin/reindex-schema")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "reindex completed"
    assert body["tables_indexed"] == 5


def test_reindex_schema_returns_500_on_exception(client):
    with patch("app.api.admin_router.IndexingService") as MockService:
        MockService.return_value.reindex.side_effect = Exception("pgvector connection failed")

        response = client.post("/api/v1/admin/reindex-schema")

    assert response.status_code == 500
    body = response.json()
    assert body["message"] == "reindex failed"
    assert body["detail"] == "pgvector connection failed"


def test_reindex_knowledge_returns_200_with_documents_indexed(client):
    """Verifica que /reindex-knowledge retorna 200 y el conteo de documentos indexados."""
    fake_docs = {
        "schema_orders": "Tabla orders ...",
        "join_orders_customers": "JOIN orders + customers ...",
        "fewshot_ventas_mes": "SELECT COUNT(*) ...",
    }
    with patch("app.api.admin_router.get_all_documents", return_value=fake_docs), \
         patch("app.api.admin_router.SchemaRepository") as MockRepo, \
         patch("app.api.admin_router.EmbeddingService"), \
         patch("app.api.admin_router.create_engine"):

        response = client.post("/api/v1/admin/reindex-knowledge")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "knowledge reindex completed"
    assert body["documents_indexed"] == 3


def test_reindex_knowledge_returns_500_on_exception(client):
    """Verifica que /reindex-knowledge retorna 500 cuando falla la ingestión."""
    with patch("app.api.admin_router.get_all_documents", side_effect=Exception("kb import error")):
        response = client.post("/api/v1/admin/reindex-knowledge")

    assert response.status_code == 500
    body = response.json()
    assert body["message"] == "knowledge reindex failed"
    assert body["detail"] == "kb import error"


def test_doc_type_from_name():
    """Verifica que _doc_type_from_name() mapea prefijos correctamente."""
    from app.api.admin_router import _doc_type_from_name

    assert _doc_type_from_name("schema_orders") == "schema"
    assert _doc_type_from_name("join_orders_customers") == "join"
    assert _doc_type_from_name("fewshot_ventas_mes") == "fewshot"
    assert _doc_type_from_name("unknown_doc") == "schema"
