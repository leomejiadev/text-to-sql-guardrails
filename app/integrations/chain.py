"""LCEL chain que conecta recuperación de schema con generación de SQL.

La cadena sigue el patrón: retriever → prompt → model → parser
donde 'retriever' es la capa de SchemaRepository (ejecutada en query_service
antes de llamar a esta chain), y aquí encadenamos prompt | model | parser.
"""
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.integrations.llm_client import LLMError, _build_anthropic_fallback, _build_llm
from app.schemas.sql_output import SQLOutput

_PROMPT_TEMPLATE = """\
Eres un experto en SQL. Dado el siguiente contexto de schema de base de datos,
genera SQL para responder la pregunta del usuario.

Schema relevante:
{schema_context}

Pregunta: {query}

{format_instructions}"""


class SQLChain:
    def __init__(self):
        # PydanticOutputParser inyecta format_instructions en el prompt para
        # que el modelo sepa exactamente el JSON schema que debe producir
        parser = PydanticOutputParser(pydantic_object=SQLOutput)
        prompt = ChatPromptTemplate.from_template(_PROMPT_TEMPLATE)
        primary = _build_llm()
        fallback = _build_anthropic_fallback()
        model = primary.with_fallbacks([fallback]) if fallback else primary
        # LCEL: prompt formatea variables → model genera texto → parser extrae SQLOutput
        self._chain = prompt | model | parser
        self._format_instructions = parser.get_format_instructions()

    def run(self, query: str, schema_context: str) -> SQLOutput:
        try:
            return self._chain.invoke(
                {
                    "query": query,
                    "schema_context": schema_context,
                    "format_instructions": self._format_instructions,
                }
            )
        except Exception as exc:
            raise LLMError(str(exc)) from exc
