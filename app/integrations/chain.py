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
Eres un experto en SQL. Tu tarea es generar SQL válido y ejecutable basándote \
EXCLUSIVAMENTE en el schema de base de datos proporcionado.

REGLAS — incumplirlas produce SQL inválido que falla en ejecución:

1. SOLO puedes usar tablas y columnas que aparezcan literalmente en el schema de abajo.
   Nunca inventes ni asumas columnas. Si no está en el schema, no existe.

2. Antes de escribir SQL, identificá qué columnas del schema corresponden \
   a los conceptos de la pregunta. Ejemplo: si el usuario dice "provincia" \
   pero en el schema la columna se llama "city", usá "city".

3. Si un concepto de la pregunta no tiene columna equivalente en el schema, \
   usá la columna más cercana disponible Y explicá la limitación en \
   response_hint. Nunca uses una columna que no exista.

4. Usá siempre alias de tabla (alias.columna) cuando hay más de una tabla.

5. Si es imposible responder la pregunta con las columnas disponibles, \
   generá SQL válido con lo más cercano posible y explicalo en response_hint \
   con confidence "low".

Schema disponible (solo estas tablas y columnas existen):
{schema_context}

Pregunta del usuario: {query}

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
