"""LCEL chain que conecta recuperación de schema con generación de SQL.

La cadena sigue el patrón: retriever → prompt → model → parser
donde 'retriever' es la capa de SchemaRepository (ejecutada en query_service
antes de llamar a esta chain), y aquí encadenamos prompt | model | parser.
"""
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.integrations.llm_client import LLMError, _build_llm
from app.schemas.sql_output import SQLOutput

_PROMPT_TEMPLATE = """\
Eres un experto en SQL para StarBrew, empresa global de cafeterías.
Tu única fuente de verdad es el schema proporcionado abajo. \
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

Schema disponible (es tu única fuente de verdad):
{schema_context}

Pregunta del usuario: {query}

{format_instructions}

IMPORTANTE: response_hint debe ser una respuesta en lenguaje natural útil para \
el usuario final — NO una descripción técnica del SQL. \
Ejemplo correcto: "Encontré 3 clientes en Buenos Aires: Juan, María y Fernando." \
Ejemplo incorrecto: "Esta consulta selecciona los nombres usando WHERE city..."
"""


class SQLChain:
    def __init__(self):
        # PydanticOutputParser inyecta format_instructions en el prompt para
        # que el modelo sepa exactamente el JSON schema que debe producir
        parser = PydanticOutputParser(pydantic_object=SQLOutput)
        prompt = ChatPromptTemplate.from_template(_PROMPT_TEMPLATE)
        model = _build_llm()
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
