"""Reindexea schemas de la DB del cliente + knowledge base hacia pgvector.

Corre en el startup (entrypoint.sh) antes de levantar uvicorn — así el API
ya tiene el índice actualizado desde el primer request.
Siempre re-indexa: los documentos del knowledge base cambian con el código,
y los schemas del cliente pueden cambiar entre deploys.
"""
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.repositories.query_repository import QueryRepository
from app.repositories.schema_repository import SchemaRepository
from app.services.embedding_service import EmbeddingService
from app.services.indexing_service import IndexingService
from knowledge_base import get_all_documents


def _doc_type_from_name(name: str) -> str:
    if name.startswith("join_"):
        return "join"
    if name.startswith("fewshot_"):
        return "fewshot"
    return "schema"


def main() -> None:
    sync_url = os.getenv("DATABASE_URL", "").replace("+asyncpg", "+psycopg2")
    if not sync_url:
        print("✗ DATABASE_URL no definida — abortando reindex")
        sys.exit(1)

    engine = create_engine(sync_url)
    emb = EmbeddingService()

    with Session(engine) as session:
        schema_repo = SchemaRepository(session=session, embedding_service=emb)

        # Paso 1: schemas desde la DB del cliente
        print("  → reindexando schemas del cliente...")
        indexing = IndexingService(
            query_repository=QueryRepository(),
            schema_repository=schema_repo,
        )
        result = indexing.reindex()
        print(f"  ✓ {result['reindexed_tables']} tablas indexadas")

        # Paso 2: knowledge base (schemas enriquecidos, joins, few-shots)
        print("  → reindexando knowledge base...")
        documents = get_all_documents()
        for name, text_content in documents.items():
            schema_repo.index_document(
                doc_type=_doc_type_from_name(name),
                name=name,
                text_content=text_content,
            )
        print(f"  ✓ {len(documents)} documentos indexados")


if __name__ == "__main__":
    main()
