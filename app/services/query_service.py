import hashlib
import os

import redis

from app.guardrails.factory import GuardrailFactory
from app.integrations.chain import SQLChain
from app.models.query_history import QueryHistory
from app.repositories.query_repository import QueryRepository
from app.repositories.schema_repository import SchemaRepository
from app.schemas.sql_output import SQLOutput
from app.schemas.sql_result import SQLResult
from app.services.embedding_service import EmbeddingService


class QueryBlockedError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class QueryService:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        schema_repository: SchemaRepository,
        query_repository: QueryRepository,
        chain: SQLChain,
        session,
    ):
        self._embedding_service = embedding_service
        self._schema_repository = schema_repository
        self._query_repository = query_repository
        self._chain = chain
        self._session = session
        # Cliente Redis lazy: se inyecta en tests para evitar conexión real
        self._redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    def process(self, query: str, user_id: str) -> SQLResult:
        # Cache key excluye user_id: el mismo texto genera el mismo SQL
        # independientemente de quién pregunta — el SQL es determinístico por query
        cache_key = hashlib.md5(query.strip().lower().encode()).hexdigest()

        cached = self._redis.get(cache_key)
        if cached:
            sql_output = SQLOutput.model_validate_json(cached)
            rows = self._query_repository.execute_sql(sql_output.sql)
            return SQLResult(
                sql=sql_output.sql,
                confidence=sql_output.confidence,
                tables_used=sql_output.tables_used,
                detected_language=sql_output.detected_language,
                response_hint=sql_output.response_hint,
                results=rows,
                row_count=len(rows),
            )

        # Paso 1: obtener embedding (para trazabilidad)
        self._embedding_service.embed(query)

        # Paso 2: recuperar tablas semánticamente relevantes via pgvector
        relevant_tables = self._schema_repository.find_relevant_tables(query)
        schema_context = "\n\n".join(t["schema_text"] for t in relevant_tables)

        # Nombres reales de tablas SQL (sin prefijos de documentos pgvector)
        valid_sql_tables = self._schema_repository.get_valid_sql_tables()

        # Paso 3: generar SQLOutput via LCEL chain
        sql_output: SQLOutput = self._chain.run(
            query=query, schema_context=schema_context
        )

        # Paso 4: ejecutar todos los guardrails; el primero que bloquea corta el pipeline
        guardrails = GuardrailFactory.get_all(valid_tables=valid_sql_tables)
        for guardrail in guardrails:
            result = guardrail.validate(sql_output)
            if result.blocked:
                self._save_history(
                    user_id, query, sql_output, was_blocked=True, block_reason=result.reason
                )
                raise QueryBlockedError(result.reason)

        # Solo cacheamos después de pasar guardrails — no cacheamos SQL bloqueado
        self._redis.setex(cache_key, 3600, sql_output.model_dump_json())

        # Paso 5: ejecutar el SELECT contra la DB del cliente y devolver datos reales
        rows = self._query_repository.execute_sql(sql_output.sql)
        self._save_history(user_id, query, sql_output, executed=True)

        return SQLResult(
            sql=sql_output.sql,
            confidence=sql_output.confidence,
            tables_used=sql_output.tables_used,
            detected_language=sql_output.detected_language,
            response_hint=sql_output.response_hint,
            results=rows,
            row_count=len(rows),
        )

    def _save_history(
        self,
        user_id: str,
        query: str,
        sql_output: SQLOutput,
        *,
        was_blocked: bool = False,
        block_reason: str | None = None,
        executed: bool = False,
    ) -> None:
        history = QueryHistory(
            user_id=user_id,
            original_query=query,
            generated_sql=sql_output.sql,
            was_blocked=was_blocked,
            block_reason=block_reason,
            executed=executed,
            detected_language=sql_output.detected_language,
        )
        self._session.add(history)
        self._session.commit()
