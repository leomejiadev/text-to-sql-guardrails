from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.query_request import QueryRequest
from app.services import tasks

router = APIRouter(tags=["queries"])

# Limiter local al router: cada router declara sus propios límites sin
# acoplarse al Limiter global de main.py. main.py lo registra como state.
limiter = Limiter(key_func=get_remote_address)


@router.post("/query", status_code=202)
@limiter.limit("10/10 minutes")
def submit_query(request: Request, body: QueryRequest) -> dict:
    """Encola la tarea y responde inmediatamente con el task_id.

    `request: Request` requerido por slowapi para leer IP. El body se renombra
    a `body` para evitar colisión con el parámetro `request` de FastAPI.
    """
    result = tasks.process_query.delay(query=body.query, user_id=body.user_id)
    return {"task_id": result.id, "status": "queued", "message": "processing"}


@router.get("/query/{task_id}")
def get_query_result(task_id: str):
    result = AsyncResult(task_id, app=tasks.celery_app)

    if not result.ready():
        # Tarea aún en cola o ejecutándose — el cliente vuelve a consultar
        return JSONResponse(status_code=202, content={"status": "processing"})

    if result.failed():
        raise HTTPException(status_code=500, detail=str(result.result))

    payload = result.result

    # QueryBlockedError fue capturado en la tarea y guardado como dict con "blocked"
    if isinstance(payload, dict) and payload.get("blocked"):
        raise HTTPException(status_code=422, detail=payload["block_reason"])

    return JSONResponse(status_code=200, content=payload)
