"""Tests del schema SQLOutput — structured output del LLM.

Este schema es el contrato que el LLM DEBE respetar cuando genera SQL.
Verificamos: `confidence` acotado a tres valores en inglés, `tables_used`
siempre como lista, y los campos de idioma (`detected_language` +
`response_hint`) como strings obligatorios para poder responder al usuario
en su mismo idioma.
"""
import pytest
from pydantic import ValidationError


def _import_schema():
    # Import tardío — mantiene el patrón TDD del resto de tests del proyecto
    # y aísla fallos de colección si el módulo aún no existiera.
    from app.schemas.sql_output import SQLOutput
    return SQLOutput


@pytest.mark.parametrize("level", ["high", "medium", "low"])
def test_confidence_accepts_all_three_valid_levels(level):
    """Los tres valores en inglés ("high", "medium", "low") deben construir
    sin error — son el contrato estable que consumen los guardrails."""
    SQLOutput = _import_schema()

    output = SQLOutput(
        sql="SELECT 1",
        confidence=level,
        tables_used=["users"],
        detected_language="en",
        response_hint="returns a constant",
    )
    assert output.confidence == level


def test_confidence_rejects_other_values():
    """Cualquier otro string (traducciones, mayúsculas, variantes) debe
    fallar. El set es cerrado porque afecta decisiones de guardrails."""
    SQLOutput = _import_schema()

    with pytest.raises(ValidationError):
        SQLOutput(
            sql="SELECT 1",
            confidence="alta",  # español — ya no permitido
            tables_used=[],
            detected_language="es",
            response_hint="devuelve una constante",
        )


def test_tables_used_is_a_list():
    """tables_used siempre es list[str] — nunca None, nunca un string suelto.
    Permite a los guardrails iterar sin chequeos defensivos."""
    SQLOutput = _import_schema()

    output = SQLOutput(
        sql="SELECT * FROM users JOIN orders ON users.id = orders.user_id",
        confidence="high",
        tables_used=["users", "orders"],
        detected_language="en",
        response_hint="joins users with their orders",
    )
    assert isinstance(output.tables_used, list)
    assert output.tables_used == ["users", "orders"]


def test_detected_language_is_required_string():
    """`detected_language` es obligatorio: el LLM debe declarar en qué idioma
    estaba la pregunta para que la respuesta al usuario salga en ese mismo
    idioma. Sin él no podemos cerrar el ciclo multilingüe."""
    SQLOutput = _import_schema()

    # Construcción válida confirma el tipo string.
    output = SQLOutput(
        sql="SELECT 1",
        confidence="high",
        tables_used=[],
        detected_language="es",
        response_hint="devuelve una constante",
    )
    assert isinstance(output.detected_language, str)
    assert output.detected_language == "es"

    # Omitirlo debe fallar la validación — es campo requerido.
    with pytest.raises(ValidationError):
        SQLOutput(
            sql="SELECT 1",
            confidence="high",
            tables_used=[],
            response_hint="returns a constant",
        )


def test_response_hint_is_required_string():
    """`response_hint` es una explicación breve del SQL en el mismo idioma
    que la pregunta original. Obligatorio: es lo que la UI muestra al
    usuario como contexto de lo que se va a ejecutar."""
    SQLOutput = _import_schema()

    output = SQLOutput(
        sql="SELECT COUNT(*) FROM users",
        confidence="high",
        tables_used=["users"],
        detected_language="en",
        response_hint="counts all users",
    )
    assert isinstance(output.response_hint, str)
    assert output.response_hint == "counts all users"

    # Omitirlo debe fallar — no hay default porque depende del idioma
    # detectado y solo el LLM puede producirlo.
    with pytest.raises(ValidationError):
        SQLOutput(
            sql="SELECT 1",
            confidence="high",
            tables_used=[],
            detected_language="en",
        )
