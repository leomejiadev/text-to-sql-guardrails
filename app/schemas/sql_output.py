"""Structured output del LLM con el SQL generado y su metadata."""
from typing import Literal

from pydantic import BaseModel


class SQLOutput(BaseModel):
    # SQL crudo; la sanitización/validación sintáctica vive en la capa de guardrails
    sql: str

    # Tres niveles (no float 0-1) — "low" puede disparar revisión humana
    confidence: Literal["high", "medium", "low"]

    # list[str] (nunca None): el LLM debe siempre declarar qué tablas usó
    tables_used: list[str]

    # Código ISO 639-1; la validación del set soportado vive en el service
    detected_language: str

    response_hint: str
