"""Cliente LLM configurable por proveedor (OpenAI o Gemini).

Usa structured output en lugar de parsing manual: la API garantiza que la
respuesta sea JSON conforme al schema de SQLOutput, eliminando errores de
parseo y reduciendo prompts de formato en el contexto.
"""
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.schemas.sql_output import SQLOutput


class LLMError(Exception):
    pass


def _build_llm():
    provider = os.getenv("LLM_PROVIDER", "gemini")
    if provider == "openai":
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    if provider == "gemini":
        return ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    raise ValueError(f"LLM_PROVIDER desconocido: {provider}")


def _build_anthropic_fallback():
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)


class LLMClient:
    def __init__(self):
        primary = _build_llm().with_structured_output(SQLOutput)
        fallback = _build_anthropic_fallback()
        # with_fallbacks: si primary lanza cualquier excepción, reintenta con Haiku
        if fallback:
            self._model = primary.with_fallbacks(
                [fallback.with_structured_output(SQLOutput)]
            )
        else:
            self._model = primary

    def generate_sql(self, query: str, schema_context: str) -> SQLOutput:
        try:
            prompt = f"Schema:\n{schema_context}\n\nPregunta: {query}\n\nGenera SQL."
            return self._model.invoke(prompt)
        except Exception as exc:
            raise LLMError(str(exc)) from exc
