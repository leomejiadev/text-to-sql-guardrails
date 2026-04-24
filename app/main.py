import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.admin_router import router as admin_router
from app.api.query_router import router as query_router

# Título visible en la doc OpenAPI — sirve como identificación humana del
# servicio cuando hay varios corriendo detrás del mismo API gateway.
app = FastAPI(title="Text to SQL with Guardrails")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Limiter centralizado con Redis: los contadores persisten entre reinicios
# y son compartidos en deployments multi-réplica. Sin storage_uri cada
# proceso tendría su propio contador y el límite sería inefectivo.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)
app.state.limiter = limiter


# Handler custom: slowapi levanta RateLimitExceeded cuando se supera el límite.
# Lo interceptamos aquí para devolver el mensaje consistente en toda la app
# en vez del mensaje genérico de slowapi.
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"message": "rate limit exceeded, try again in 10 minutes"},
    )


# /api/v1 como prefijo de versión: permite introducir /api/v2 en el futuro
# sin romper clientes existentes. Los routers no conocen su propio prefix
# a propósito — así son reusables bajo cualquier montaje.
app.include_router(query_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1/admin")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check mínimo para probes de Kubernetes/Docker.

    Devuelve 200 con un payload fijo — no toca DB ni Redis a propósito:
    un health check liveness debe responder incluso si las dependencias
    están caídas, para distinguir "proceso vivo" de "dependencia rota".
    """
    # dict literal en vez de un schema Pydantic: el contrato es trivial y
    # no queremos acoplar /health a la capa de schemas.
    return {"status": "ok"}
