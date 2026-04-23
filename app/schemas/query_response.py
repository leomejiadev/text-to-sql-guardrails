"""Schema de respuesta del endpoint POST /query.

Formato mínimo para que el cliente pueda hacer polling de una tarea
Celery: task_id para consultar, status para el estado actual y message
para mostrarle al usuario.
"""
from pydantic import BaseModel


class QueryResponse(BaseModel):
    """Ack inmediato del endpoint: la query ya está encolada, acá tenés
    cómo seguirla."""

    # str en vez de UUID: el task_id viene de Celery y queremos aceptar
    # cualquier formato de id que Celery use en su backend.
    task_id: str

    # str (no Enum) en Fase 1: el set de estados todavía se está cerrando.
    # Cuando se estabilice se cambia a Literal["queued","processing","done",...]
    status: str

    # Mensaje legible para la UI — no se usa para lógica, solo display.
    message: str
