import importlib
from unittest.mock import patch


def test_reindex_schema_task_calls_reindex_once():
    with patch("app.services.tasks.IndexingService") as MockService:
        MockService.return_value.reindex.return_value = 3

        from app.services.tasks import reindex_schema
        reindex_schema()

        MockService.return_value.reindex.assert_called_once()


def test_schedule_reads_reindex_interval_from_env(monkeypatch):
    monkeypatch.setenv("REINDEX_INTERVAL_SECONDS", "3600")

    # Reimportamos el módulo para que lea la variable de entorno actualizada
    import app.services.tasks as tasks_module
    importlib.reload(tasks_module)

    schedule = tasks_module.celery_app.conf.beat_schedule
    # total_seconds() porque timedelta.seconds solo tiene el componente <1 día
    interval = schedule["reindex-schema-periodic"]["schedule"].total_seconds()
    assert interval == 3600


def test_schedule_default_is_86400(monkeypatch):
    monkeypatch.delenv("REINDEX_INTERVAL_SECONDS", raising=False)

    import app.services.tasks as tasks_module
    importlib.reload(tasks_module)

    schedule = tasks_module.celery_app.conf.beat_schedule
    interval = schedule["reindex-schema-periodic"]["schedule"].total_seconds()
    assert interval == 86400
