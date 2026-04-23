from app.guardrails.sensitive_validator import SensitiveDataValidator
from app.schemas.sql_output import SQLOutput


def _make_output(sql: str, tables: list[str] | None = None) -> SQLOutput:
    return SQLOutput(
        sql=sql,
        confidence="high",
        tables_used=tables or ["users"],
        detected_language="en",
        response_hint="test",
    )


def test_blocks_password_column_in_sql():
    result = SensitiveDataValidator().validate(
        _make_output("SELECT password FROM users")
    )
    assert result.blocked is True
    assert "password" in result.reason


def test_blocks_salary_table_in_tables_used():
    result = SensitiveDataValidator().validate(
        _make_output("SELECT * FROM salary_data", tables=["salary_data"])
    )
    assert result.blocked is True
    assert "salary" in result.reason


def test_passes_clean_sql_no_sensitive_patterns():
    result = SensitiveDataValidator().validate(
        _make_output("SELECT id, name, email FROM customers", tables=["customers"])
    )
    assert result.blocked is False
    assert result.reason is None
