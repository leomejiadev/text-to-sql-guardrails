from app.guardrails.base import BaseGuardrail, GuardrailResult
from app.schemas.sql_output import SQLOutput


class SchemaValidator(BaseGuardrail):
    def __init__(self, valid_tables: set[str]):
        self._valid_tables = valid_tables

    def validate(self, sql_output: SQLOutput) -> GuardrailResult:
        invalid = [t for t in sql_output.tables_used if t not in self._valid_tables]
        if invalid:
            return GuardrailResult(
                blocked=True,
                reason=f"Tablas no registradas en el schema: {', '.join(invalid)}",
            )
        return GuardrailResult(blocked=False, reason=None)
