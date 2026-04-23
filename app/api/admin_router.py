"""Router de operaciones administrativas — no expuesto a usuarios finales.

Está separado de `query_router` porque tiene un perfil de seguridad
distinto: en producción requiere auth estricta (p. ej. service-to-service)
y sus endpoints mutan estado compartido (el índice de schema, caches).
Mantenerlos en otro router permite aplicarles middlewares diferentes sin
contaminar el flujo del usuario final.
"""
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.repositories.query_repository import QueryRepository
from app.repositories.schema_repository import SchemaRepository
from app.services.embedding_service import EmbeddingService
from app.services.indexing_service import IndexingService

# TODO: agregar API key auth antes de deploy a producción
router = APIRouter(tags=["admin"])

# Limiter local al router: cada router declara sus propios límites sin
# acoplarse al Limiter global de main.py. main.py lo registra como state.
limiter = Limiter(key_func=get_remote_address)


@router.post("/reindex-schema")
@limiter.limit("5/10 minutes")
async def reindex_schema(request: Request) -> JSONResponse:
    """Re-indexa el schema de la DB destino en el vector store.

    `request: Request` es requerido por slowapi para leer la IP del cliente.
    FastAPI lo inyecta automáticamente — no aparece en el schema OpenAPI.
    """
    try:
        sync_url = os.getenv("DATABASE_URL", "").replace("+asyncpg", "+psycopg2")
        engine = create_engine(sync_url)
        emb = EmbeddingService()
        with Session(engine) as session:
            service = IndexingService(
                query_repository=QueryRepository(),
                schema_repository=SchemaRepository(session=session, embedding_service=emb),
            )
            tables_indexed = service.reindex()
        return JSONResponse(
            status_code=200,
            content={"message": "reindex completed", "tables_indexed": tables_indexed},
        )
    except Exception as e:
        # Capturamos cualquier excepción para no exponer stack traces al cliente
        return JSONResponse(
            status_code=500,
            content={"message": "reindex failed", "detail": str(e)},
        )
