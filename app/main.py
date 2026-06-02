import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.admin_router import router as admin_router
from app.api.query_router import router as query_router

app = FastAPI(title="Text to SQL with Guardrails")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
)

# Limiter centralizado con Redis: los contadores persisten entre reinicios
# y son compartidos en deployments multi-réplica. Sin storage_uri cada
# proceso tendría su propio contador y el límite sería inefectivo.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)
app.state.limiter = limiter


# Handler custom para devolver un mensaje consistente en toda la app
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"message": "rate limit exceeded, try again in 10 minutes"},
    )


app.include_router(query_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1/admin")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check de liveness — responde 200 sin tocar dependencias."""
    return {"status": "ok"}
