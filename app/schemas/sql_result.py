from typing import Any

from pydantic import BaseModel


class SQLResult(BaseModel):
    sql: str
    confidence: str
    tables_used: list[str]
    detected_language: str
    response_hint: str
    results: list[dict[str, Any]]
    row_count: int
