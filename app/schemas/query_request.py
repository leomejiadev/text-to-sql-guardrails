"""Schema de entrada del endpoint POST /query."""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    # min=3 descarta inputs triviales ('hi', '?'); max=500 acota el costo del LLM
    query: str = Field(min_length=3, max_length=500)

    user_id: str
