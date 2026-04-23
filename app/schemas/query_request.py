"""Schema de entrada del endpoint POST /query.

Vive en `schemas/` (no en `models/`) porque representa el contrato con el
cliente, no una tabla de DB. Si mañana el storage cambia, este schema no
tiene por qué cambiar con él.
"""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    # min=3 descarta inputs triviales ('hi', '?'); max=500 acota el costo
    # del LLM y evita que se mande un documento entero como pregunta.
    query: str = Field(min_length=3, max_length=500)

    # user_id viene del sistema de auth aguas arriba: el schema solo valida
    # su presencia, la autorización real es responsabilidad de otra capa.
    user_id: str
