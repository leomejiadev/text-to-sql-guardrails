"""Tests de SQLChain — estructura del prompt, config de observabilidad y firma trace_id."""
from unittest.mock import MagicMock

import pytest
from langchain_core.prompts import (
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from app.integrations.chain import SQLChain
from app.schemas.sql_output import SQLOutput


@pytest.fixture(autouse=True)
def _anthropic_key(monkeypatch):
    # ChatAnthropic exige la env var en construcción; un valor dummy basta
    # porque nunca invocamos al LLM real en estos unit tests.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture
def fake_sql_output() -> SQLOutput:
    return SQLOutput(
        sql="SELECT 1",
        confidence="high",
        tables_used=["t"],
        detected_language="es",
        response_hint="ok",
    )


@pytest.fixture
def chain_with_mocked_invoke(fake_sql_output) -> SQLChain:
    # Reemplazamos el RunnableSequence interno para no llamar al LLM real
    chain = SQLChain()
    chain._chain = MagicMock()
    chain._chain.invoke.return_value = fake_sql_output
    return chain


class TestSQLChainPromptStructure:
    def test_prompt_uses_from_messages_with_system_and_human(self):
        # from_messages produce un ChatPromptTemplate con messages tipados;
        # from_template colapsa todo a un solo HumanMessagePromptTemplate.
        chain = SQLChain()
        messages = chain._prompt.messages
        assert len(messages) == 2
        assert isinstance(messages[0], SystemMessagePromptTemplate)
        assert isinstance(messages[1], HumanMessagePromptTemplate)


class TestSQLChainObservabilityConfig:
    def test_chain_exposes_run_name(self):
        chain = SQLChain()
        config = chain._chain.config
        assert config.get("run_name") == "sql-generation-chain"

    def test_chain_exposes_production_and_text_to_sql_tags(self):
        chain = SQLChain()
        tags = chain._chain.config.get("tags") or []
        assert "production" in tags
        assert "text-to-sql" in tags

    def test_chain_exposes_version_metadata(self):
        chain = SQLChain()
        metadata = chain._chain.config.get("metadata") or {}
        assert metadata.get("version") == "1.0"


class TestSQLChainRunSignature:
    def test_run_without_trace_id_remains_backward_compatible(
        self, chain_with_mocked_invoke, fake_sql_output
    ):
        # Firma vieja (sin trace_id) debe seguir funcionando — los tests
        # existentes de query_service llaman así.
        result = chain_with_mocked_invoke.run(query="q", schema_context="s")
        assert result == fake_sql_output

    def test_run_accepts_optional_trace_id(
        self, chain_with_mocked_invoke, fake_sql_output
    ):
        # trace_id es opcional; debe aceptarse sin alterar el resultado.
        result = chain_with_mocked_invoke.run(
            query="q", schema_context="s", trace_id="abc-123"
        )
        assert result == fake_sql_output
