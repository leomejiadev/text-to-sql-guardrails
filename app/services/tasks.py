import logging
import os

from celery import Celery
from celery.schedules import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.integrations.chain import SQLChain
from app.integrations.llm_client import LLMError
from app.repositories.query_repository import QueryRepository
from app.repositories.schema_repository import SchemaRepository
from app.schemas.sql_output import SQLOutput
from app.services.embedding_service import EmbeddingService
from app.services.indexing_service import IndexingService
from app.services.query_service import QueryBlockedError, QueryService

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Leído en tiempo de importación: Beat registra el schedule una sola vez al
# arrancar, por eso no alcanza con leerlo dentro de la tarea.
REINDEX_INTERVAL_SECONDS = int(os.getenv("REINDEX_INTERVAL_SECONDS", "86400"))

celery_app = Celery(
    "text_to_sql",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        "reindex-schema-periodic": {
            "task": "app.services.tasks.reindex_schema",
            "schedule": timedelta(seconds=REINDEX_INTERVAL_SECONDS),
        },
    },
)


def _run_pipeline(query: str, user_id: str) -> SQLOutput:
    """Construye todas las dependencias y ejecuta el pipeline sincrónico.

    Función separada para permitir mocking limpio en tests unitarios.
    """
    # asyncpg no soporta uso sincrónico; psycopg2 es el driver sync
    sync_url = os.getenv("DATABASE_URL", "").replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    emb = EmbeddingService()
    with Session(engine) as session:
        service = QueryService(
            embedding_service=emb,
            schema_repository=SchemaRepository(session=session, embedding_service=emb),
            query_repository=QueryRepository(),
            chain=SQLChain(),
            session=session,
        )
        return service.process(query, user_id)


@celery_app.task(bind=True, max_retries=3)
def process_query(self, query: str, user_id: str) -> dict:
    try:
        result: SQLOutput = _run_pipeline(query, user_id)
        return result.model_dump()
    except QueryBlockedError as exc:
        # Bloqueo es resultado esperado del negocio — no debe crashear el worker
        return {"blocked": True, "block_reason": exc.reason}
    except LLMError as exc:
        # Backoff exponencial: 30s en retry 0, 60s en retry 1, 120s en retry 2
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


@celery_app.task
def reindex_schema() -> None:
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
        logger.info("reindex completado: %d tablas indexadas", tables_indexed)
    except Exception as exc:
        # Se loggea aquí y no se propaga: propagar mataría el worker de Beat
        # y detendría todos los schedules hasta reinicio manual. El próximo
        # ciclo programado reintentará automáticamente sin intervención.
        logger.error(
            "reindex_schema falló | tarea=reindex_schema | error=%s",
            exc,
            exc_info=True,
        )
