from app.guardrails.schema_validator import SchemaValidator
from app.schemas.sql_output import SQLOutput


def _make_output(tables: list[str]) -> SQLOutput:
    return SQLOutput(
        sql="SELECT * FROM t",
        confidence="high",
        tables_used=tables,
        detected_language="en",
        response_hint="test",
    )


def test_blocks_unregistered_table():
    validator = SchemaValidator(valid_tables={"orders", "products"})
    result = validator.validate(_make_output(["orders", "unknown_table"]))
    assert result.blocked is True
    assert "unknown_table" in result.reason


def test_passes_when_all_tables_valid():
    validator = SchemaValidator(valid_tables={"orders", "products"})
    result = validator.validate(_make_output(["orders", "products"]))
    assert result.blocked is False
    assert result.reason is None
