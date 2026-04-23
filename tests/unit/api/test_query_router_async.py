"""Tests para el router asíncrono con Celery (Fase 4)."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


class TestPostQueryAsync:

    def test_post_query_returns_202_with_task_id(self, client):
        """POST /query debe encolar la tarea y responder 202 inmediatamente."""
        mock_result = MagicMock()
        mock_result.id = "task-abc-123"

        with patch("app.api.query_router.tasks.process_query") as mock_task:
            mock_task.delay.return_value = mock_result

            resp = client.post(
                "/api/v1/query",
                json={"query": "show all users", "user_id": "u1"},
            )

        assert resp.status_code == 202
        body = resp.json()
        assert body["task_id"] == "task-abc-123"
        assert body["status"] == "queued"
        assert body["message"] == "processing"

    def test_get_query_task_processing_returns_202(self, client):
        """GET /query/{task_id} debe devolver 202 si la tarea aún no terminó."""
        mock_result = MagicMock()
        mock_result.ready.return_value = False

        with patch("app.api.query_router.AsyncResult", return_value=mock_result):
            resp = client.get("/api/v1/query/task-abc-123")

        assert resp.status_code == 202
        assert resp.json()["status"] == "processing"

    def test_get_query_task_ready_returns_200_with_result(self, client):
        """GET /query/{task_id} debe devolver 200 con el resultado cuando está listo."""
        mock_result = MagicMock()
        mock_result.ready.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {
            "sql": "SELECT * FROM users",
            "detected_language": "en",
            "confidence": "high",
            "tables_used": ["users"],
            "response_hint": "Lista completa",
        }

        with patch("app.api.query_router.AsyncResult", return_value=mock_result):
            resp = client.get("/api/v1/query/task-abc-123")

        assert resp.status_code == 200
        assert resp.json()["sql"] == "SELECT * FROM users"

    def test_get_query_task_blocked_returns_422(self, client):
        """GET /query/{task_id} debe devolver 422 con block_reason si fue bloqueado."""
        mock_result = MagicMock()
        mock_result.ready.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {
            "blocked": True,
            "block_reason": "SQL injection detected",
        }

        with patch("app.api.query_router.AsyncResult", return_value=mock_result):
            resp = client.get("/api/v1/query/task-abc-123")

        assert resp.status_code == 422
        assert resp.json()["detail"] == "SQL injection detected"
