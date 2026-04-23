"""Schema de structured output del LLM.

Contrato que el LLM debe respetar al generar SQL. Pydantic se encarga
de la validación: si el modelo devuelve JSON que no encaja, la llamada
falla aguas arriba y el request se marca como bloqueado.

Incluye metadata de idioma (`detected_language` + `response_hint`) para
poder responder al usuario en el mismo idioma en que preguntó, cerrando
el ciclo multilingüe sin una segunda llamada al LLM.
"""
from typing import Literal

from pydantic import BaseModel


class SQLOutput(BaseModel):
    # SQL crudo tal como lo devuelve el modelo. La sanitización/validación
    # sintáctica vive en la capa de guardrails, no acá.
    sql: str

    # Literal en inglés: es el set estable que consumen los guardrails.
    # Tres niveles (y no un float 0-1) para simplificar la lógica:
    # "low" puede disparar revisión humana, "high" ejecuta directo.
    confidence: Literal["high", "medium", "low"]

    # list[str] (nunca None): el default se omite a propósito — queremos
    # que el LLM siempre declare qué tablas usó, aunque sea lista vacía.
    tables_used: list[str]

    # Código ISO 639-1 ("en", "es", "pt", ...). Obligatorio: sin él no
    # sabemos en qué idioma responder. La validación del set concreto de
    # idiomas soportados vive en la capa de servicio, no en el schema.
    detected_language: str

    # Explicación breve del SQL en el mismo idioma que `detected_language`.
    # Obligatorio: la UI lo muestra al usuario como contexto de lo que el
    # sistema entendió antes de ejecutar la query.
    response_hint: str
