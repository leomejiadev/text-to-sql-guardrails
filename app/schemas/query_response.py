"""Schema de respuesta del endpoint POST /query."""
from pydantic import BaseModel


class QueryResponse(BaseModel):
    # str en vez de UUID: aceptamos cualquier formato de id que Celery use en su backend
    task_id: str

    # TODO: cambiar a Literal cuando el set de estados se estabilice
    status: str

    message: str
