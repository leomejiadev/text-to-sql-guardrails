"""Tests del schema QueryRequest.

Validamos las reglas de entrada del endpoint POST /query: Pydantic debe
rechazar `query` fuera del rango [3, 500] caracteres y aceptar un payload
bien formado.
"""
import pytest
from pydantic import ValidationError


def _import_schema():
    # Import tardío — el módulo aún no existe cuando este test se escribe.
    from app.schemas.query_request import QueryRequest
    return QueryRequest


def test_query_shorter_than_3_chars_fails():
    """Pydantic debe rechazar queries demasiado cortas (p. ej. '?') para
    evitar desperdiciar llamadas al LLM con prompts sin contenido real."""
    QueryRequest = _import_schema()

    with pytest.raises(ValidationError):
        QueryRequest(query="ab", user_id="user-1")


def test_query_longer_than_500_chars_fails():
    """Cota superior para contener el costo del LLM y evitar que un usuario
    mande un documento entero como 'pregunta'."""
    QueryRequest = _import_schema()

    too_long = "a" * 501
    with pytest.raises(ValidationError):
        QueryRequest(query=too_long, user_id="user-1")


def test_valid_request_passes():
    """Caso happy path: query dentro del rango y user_id presente."""
    QueryRequest = _import_schema()

    request = QueryRequest(
        query="how many orders does user 42 have?",
        user_id="user-42",
    )
    assert request.query == "how many orders does user 42 have?"
    assert request.user_id == "user-42"
