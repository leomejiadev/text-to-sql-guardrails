"""Cliente LLM configurable por proveedor (OpenAI o Gemini).

Usa structured output en lugar de parsing manual: la API garantiza que la
respuesta sea JSON conforme al schema de SQLOutput, eliminando errores de
parseo y reduciendo prompts de formato en el contexto.
"""
import os

from langchain_anthropic import ChatAnthropic

from app.schemas.sql_output import SQLOutput


class LLMError(Exception):
    pass


def _build_llm():
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("La variable de entorno ANTHROPIC_API_KEY no está configurada.")
    return ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0
    )


class LLMClient:
    def __init__(self):
        self._model = _build_llm().with_structured_output(SQLOutput)

    def generate_sql(self, query: str, schema_context: str) -> SQLOutput:
        try:
            prompt = f"Schema:\n{schema_context}\n\nPregunta: {query}\n\nGenera SQL."
            return self._model.invoke(prompt)
        except Exception as exc:
            raise LLMError(str(exc)) from exc
