"""Tests del schema QueryResponse.

Contrato de salida del endpoint POST /query cuando la petición se encola
en Celery. Verificamos que el schema expone los tres campos que el
cliente necesita para hacer polling del estado de la tarea.
"""
from pydantic import BaseModel


def _import_schema():
    from app.schemas.query_response import QueryResponse
    return QueryResponse


def test_response_has_task_id_status_and_message():
    """El response debe tener exactamente estos tres campos — es lo que el
    cliente consume para saber qué task_id hacer polling y mostrar estado."""
    QueryResponse = _import_schema()

    response = QueryResponse(
        task_id="abc-123",
        status="queued",
        message="Query queued for processing",
    )

    assert response.task_id == "abc-123"
    assert response.status == "queued"
    assert response.message == "Query queued for processing"

    # Doble guardia: el schema debe ser un Pydantic BaseModel para que
    # FastAPI lo serialice automáticamente en la respuesta HTTP.
    assert isinstance(response, BaseModel)
