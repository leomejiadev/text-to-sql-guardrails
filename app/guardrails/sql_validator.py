import re

from app.guardrails.base import BaseGuardrail, GuardrailResult
from app.schemas.sql_output import SQLOutput

_DESTRUCTIVE = ["DROP", "DELETE", "UPDATE", "TRUNCATE", "ALTER", "INSERT"]


class SqlValidator(BaseGuardrail):
    def validate(self, sql_output: SQLOutput) -> GuardrailResult:
        # \b evita falsos positivos (ej. "INSERTED" no activa "INSERT")
        for keyword in _DESTRUCTIVE:
            if re.search(rf"\b{keyword}\b", sql_output.sql, re.IGNORECASE):
                return GuardrailResult(
                    blocked=True,
                    reason=f"SQL contiene operación destructiva: {keyword}",
                )
        return GuardrailResult(blocked=False, reason=None)
