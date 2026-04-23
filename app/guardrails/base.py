from dataclasses import dataclass

from app.schemas.sql_output import SQLOutput


@dataclass
class GuardrailResult:
    blocked: bool
    reason: str | None


class BaseGuardrail:
    def validate(self, sql_output: SQLOutput) -> GuardrailResult:
        raise NotImplementedError
