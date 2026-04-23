"""Factory Pattern para instanciar guardrails sin modificar la capa de servicios."""
from app.guardrails.base import BaseGuardrail
from app.guardrails.schema_validator import SchemaValidator
from app.guardrails.sensitive_validator import SensitiveDataValidator
from app.guardrails.sql_validator import SqlValidator


class GuardrailFactory:
    # Lista estática de clases — agregar un validator aquí es suficiente para activarlo
    _guardrails = [SqlValidator, SchemaValidator, SensitiveDataValidator]

    @classmethod
    def get_all(cls, valid_tables: set[str]) -> list[BaseGuardrail]:
        return [
            SqlValidator(),
            SchemaValidator(valid_tables=valid_tables),
            SensitiveDataValidator(),
        ]
