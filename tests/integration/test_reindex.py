import pytest
from celery.schedules import timedelta
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    return TestClient(app)


def test_reindex_endpoint_indexes_tables_in_pgvector(client, db_session):
    """Llama al endpoint real y verifica que haya filas en la tabla de embeddings."""
    from sqlalchemy import text

    response = client.post("/api/v1/admin/reindex-schema")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "reindex completed"
    assert body["tables_indexed"] > 0

    # schema_embeddings usa SQL raw (sin SQLModel), consultamos directo
    result = db_session.execute(text("SELECT COUNT(*) FROM schema_embeddings"))
    count = result.scalar()
    assert count > 0


def test_celery_beat_registers_reindex_task_with_correct_interval():
    """Verifica que Beat tenga la tarea periódica registrada con el intervalo correcto."""
    from app.services.tasks import celery_app

    schedule = celery_app.conf.beat_schedule
    assert "reindex-schema-periodic" in schedule

    task_config = schedule["reindex-schema-periodic"]
    assert task_config["task"] == "app.services.tasks.reindex_schema"
    assert isinstance(task_config["schedule"], timedelta)
    # El default es 86400s — en CI no hay REINDEX_INTERVAL_SECONDS definido
    assert task_config["schedule"].total_seconds() == 86400
