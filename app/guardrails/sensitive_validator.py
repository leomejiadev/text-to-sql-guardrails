from app.guardrails.base import BaseGuardrail, GuardrailResult
from app.schemas.sql_output import SQLOutput

_SENSITIVE_PATTERNS = ["password", "secret", "token", "credit_card", "ssn", "salary"]


class SensitiveDataValidator(BaseGuardrail):
    def validate(self, sql_output: SQLOutput) -> GuardrailResult:
        sql_lower = sql_output.sql.lower()
        for pattern in _SENSITIVE_PATTERNS:
            if pattern in sql_lower:
                return GuardrailResult(
                    blocked=True,
                    reason=f"SQL accede a dato sensible: {pattern}",
                )
        for table in sql_output.tables_used:
            for pattern in _SENSITIVE_PATTERNS:
                if pattern in table.lower():
                    return GuardrailResult(
                        blocked=True,
                        reason=f"Tabla sensible detectada: {table}",
                    )
        return GuardrailResult(blocked=False, reason=None)
