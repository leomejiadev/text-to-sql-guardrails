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
        MockService.return_value.reindex.return_value = 5

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
