from app.guardrails.factory import GuardrailFactory
from app.guardrails.base import BaseGuardrail


def test_get_all_returns_three_validators():
    validators = GuardrailFactory.get_all(valid_tables={"orders"})
    assert len(validators) == 3


def test_all_inherit_from_base_guardrail():
    validators = GuardrailFactory.get_all(valid_tables={"orders"})
    for v in validators:
        assert isinstance(v, BaseGuardrail)
