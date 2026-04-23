from sqlalchemy import text

from app.services.embedding_service import EmbeddingService


class SchemaRepository:
    def __init__(self, session, embedding_service: EmbeddingService):
        # Inyección de dependencias: permite mockear session y embedding en tests
        self._session = session
        self._embedding = embedding_service

    def index_schema(self, table_name: str, schema_text: str) -> None:
        vector = self._embedding.embed(schema_text)
        # str([0.1, 0.2, ...]) produce "[0.1, 0.2, ...]", formato nativo de pgvector
        vec_str = str(vector)

        self._session.execute(
            text("""
                INSERT INTO schema_embeddings (table_name, schema_text, embedding)
                VALUES (:table_name, :schema_text, (:vec)::vector)
                ON CONFLICT (table_name)
                DO UPDATE SET
                    schema_text = EXCLUDED.schema_text,
                    embedding   = EXCLUDED.embedding,
                    updated_at  = now()
            """),
            {"table_name": table_name, "schema_text": schema_text, "vec": vec_str},
        )
        self._session.commit()

    def find_relevant_tables(self, query: str) -> list[str]:
        vector = self._embedding.embed(query)
        vec_str = str(vector)

        # <=> es el operador de cosine distance de pgvector
        rows = self._session.execute(
            text("""
                SELECT table_name
                FROM schema_embeddings
                ORDER BY embedding <=> (:vec)::vector
                LIMIT 4
            """),
            {"vec": vec_str},
        )
        return [row.table_name for row in rows]

    def reindex_all(self, schemas: dict[str, str]) -> None:
        for table_name, schema_text in schemas.items():
            self.index_schema(table_name, schema_text)
