"""Tests del modelo QueryHistory.

Red phase: estos tests se escriben ANTES del modelo. Validan el contrato
mínimo — campos requeridos, tipos y defaults — sin depender de la base de
datos (se instancian en memoria).
"""
from datetime import datetime
from uuid import UUID

import pytest


# Import tardío dentro del helper para no fallar la colección antes de
# que exista el módulo (estamos en TDD, aún no implementado).
def _import_model():
    from app.models.query_history import QueryHistory
    return QueryHistory


def test_has_all_required_fields():
    """El modelo debe exponer el conjunto completo de atributos definidos
    en el contrato de la Fase 1."""
    QueryHistory = _import_model()

    instance = QueryHistory(
        user_id="user-123",
        original_query="how many users are there?",
        generated_sql="SELECT COUNT(*) FROM users;",
        block_reason=None,
    )

    expected_fields = (
        "id",
        "user_id",
        "original_query",
        "generated_sql",
        "was_blocked",
        "block_reason",
        "executed",
        "created_at",
        "detected_language",
    )
    for field in expected_fields:
        assert hasattr(instance, field), f"missing field {field!r}"

    # id debe ser UUID autogenerado.
    assert isinstance(instance.id, UUID)

    # created_at debe tener default = datetime actual.
    assert isinstance(instance.created_at, datetime)


def test_was_blocked_defaults_to_false():
    """Si no se pasa `was_blocked`, el default debe ser False — representa
    el caso normal en que la query no fue bloqueada por guardrails."""
    QueryHistory = _import_model()

    instance = QueryHistory(
        user_id="user-123",
        original_query="list products",
    )
    assert instance.was_blocked is False


def test_executed_defaults_to_false():
    """Si no se pasa `executed`, el default debe ser False — una query recién
    creada todavía no se corrió contra la DB."""
    QueryHistory = _import_model()

    instance = QueryHistory(
        user_id="user-123",
        original_query="list products",
    )
    assert instance.executed is False


def test_detected_language_defaults_to_none():
    """`detected_language` es nullable: cuando se crea el registro todavía
    no se corrió la detección de idioma. La capa service lo completa."""
    QueryHistory = _import_model()

    instance = QueryHistory(
        user_id="user-123",
        original_query="list products",
    )
    assert instance.detected_language is None


@pytest.mark.parametrize("code", ["en", "es"])
def test_detected_language_accepts_iso_codes(code):
    """El campo acepta códigos ISO 639-1. La validación estricta del set
    permitido vive en la capa de detección, no en el modelo de DB."""
    QueryHistory = _import_model()

    instance = QueryHistory(
        user_id="user-123",
        original_query="list products",
        detected_language=code,
    )
    assert instance.detected_language == code
