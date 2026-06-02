"""LCEL chain que genera SQL estructurado a partir de un schema y una consulta del usuario."""
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.integrations.llm_client import LLMError, _build_llm
from app.schemas.sql_output import SQLOutput

_SYSTEM_PROMPT = """\
Eres un experto en SQL para StarBrew, empresa global de cafeterías.
Tu única fuente de verdad es el schema proporcionado por el usuario. \
Nunca uses columnas que no aparezcan literalmente en ese schema.

REGLAS CRÍTICAS:
1. Antes de escribir SQL, leé el schema completo e identificá cada columna exacta.
2. NUNCA asumas columnas por intuición. Si el schema dice 'city_id' no existe 'city'.
3. Para ubicaciones SIEMPRE hacer JOIN con cities, countries o continents — \
los clientes, sucursales y empleados tienen 'city_id', no 'city' directamente.
4. Usá alias de tabla en todos los JOINs.
5. Filtrá siempre por status = 'completed' en orders salvo que se pida lo contrario.
6. Para fechas relativas ('este mes', 'enero') usá DATE_TRUNC o EXTRACT.
7. Si es imposible responder con el schema disponible, explicalo en response_hint \
con confidence 'low'.

EJEMPLO CRÍTICO — error común a evitar:
  ❌ SELECT name FROM customers WHERE city = 'Buenos Aires'
  ✅ SELECT c.name FROM customers c
     JOIN cities ci ON ci.id = c.city_id
     WHERE ci.name = 'Buenos Aires'

IMPORTANTE: response_hint debe ser una respuesta en lenguaje natural útil para \
el usuario final — NO una descripción técnica del SQL. \
Ejemplo correcto: "Encontré 3 clientes en Buenos Aires: Juan, María y Fernando." \
Ejemplo incorrecto: "Esta consulta selecciona los nombres usando WHERE city..."
"""

_HUMAN_PROMPT = """\
Schema disponible (es tu única fuente de verdad):
{schema_context}

Pregunta del usuario: {query}

{format_instructions}
"""


class SQLChain:
    def __init__(self):
        parser = PydanticOutputParser(pydantic_object=SQLOutput)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", _SYSTEM_PROMPT),
                ("human", _HUMAN_PROMPT),
            ]
        )
        model = _build_llm()
        self._prompt = prompt
        self._chain = (prompt | model | parser).with_config(
            run_name="sql-generation-chain",
            tags=["production", "text-to-sql"],
            metadata={"version": "1.0"},
        )
        self._format_instructions = parser.get_format_instructions()

    def run(
        self,
        query: str,
        schema_context: str,
        trace_id: str | None = None,
    ) -> SQLOutput:
        config = {"metadata": {"trace_id": trace_id}} if trace_id else {}
        try:
            return self._chain.invoke(
                {
                    "query": query,
                    "schema_context": schema_context,
                    "format_instructions": self._format_instructions,
                },
                config=config,
            )
        except Exception as exc:
            raise LLMError(str(exc)) from exc
