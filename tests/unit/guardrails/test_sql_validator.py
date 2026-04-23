import pytest
from app.guardrails.sql_validator import SqlValidator
from app.schemas.sql_output import SQLOutput


def _make_output(sql: str) -> SQLOutput:
    return SQLOutput(
        sql=sql,
        confidence="high",
        tables_used=["users"],
        detected_language="en",
        response_hint="test",
    )


def test_blocks_drop_table():
    result = SqlValidator().validate(_make_output("DROP TABLE users"))
    assert result.blocked is True
    assert "DROP" in result.reason


def test_blocks_delete_from():
    result = SqlValidator().validate(_make_output("DELETE FROM users WHERE id = 1"))
    assert result.blocked is True
    assert "DELETE" in result.reason


def test_blocks_update():
    result = SqlValidator().validate(_make_output("UPDATE users SET name = 'x'"))
    assert result.blocked is True
    assert "UPDATE" in result.reason


def test_passes_clean_select():
    result = SqlValidator().validate(_make_output("SELECT * FROM users"))
    assert result.blocked is False
    assert result.reason is None
