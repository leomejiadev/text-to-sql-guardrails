import hashlib
import os
import sys
from typing import Callable, TypeVar

import redis

from app.guardrails.factory import GuardrailFactory
from app.integrations.chain import SQLChain
from app.models.query_history import QueryHistory
from app.repositories.query_repository import QueryRepository
from app.repositories.schema_repository import SchemaRepository
from app.schemas.sql_output import SQLOutput
from app.schemas.sql_result import SQLResult
from app.services.embedding_service import EmbeddingService

# Imports opcionales: si langsmith no está disponible dejamos stubs no-op
# para que el pipeline siga funcionando sin observabilidad.
try:
    from langsmith import trace as ls_trace, traceable  # type: ignore
except Exception:  # pragma: no cover — defensivo, langsmith es dep declarada
    ls_trace = None  # type: ignore

    def traceable(*decorator_args, **decorator_kwargs):  # type: ignore
        # Soporta tanto @traceable como @traceable(run_type=..., name=...)
        if decorator_args and callable(decorator_args[0]):
            return decorator_args[0]

        def _decorator(fn):
            return fn

        return _decorator

T = TypeVar("T")


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

    def _traced(
        self,
        name: str,
        fn: Callable[[], T],
        *,
        metadata: dict | None = None,
        inputs: dict | None = None,
        outputs_fn: Callable[[T], dict] | None = None,
    ) -> T:
        """Ejecuta fn() como run hijo de LangSmith sin afectar el pipeline ante fallos de observabilidad."""
        if ls_trace is None:
            return fn()

        try:
            ctx = ls_trace(
                name=name,
                run_type="chain",
                project_name=os.getenv("LANGCHAIN_PROJECT"),
                metadata=metadata or {},
                inputs=inputs or {},
            )
        except Exception:
            return fn()

        try:
            run = ctx.__enter__()
        except Exception:
            return fn()

        try:
            result = fn()
        except Exception:
            # Cerrar el run propagando la excepción real al __exit__ de LangSmith
            try:
                ctx.__exit__(*sys.exc_info())
            except Exception:
                pass
            raise

        # outputs_fn se aísla: un fallo computando outputs no debe romper el pipeline
        if outputs_fn is not None:
            try:
                run.outputs = outputs_fn(result)
            except Exception:
                pass

        try:
            ctx.__exit__(None, None, None)
        except Exception:
            pass
        return result

    @traceable(run_type="chain", name="query-pipeline")
    def process(
        self,
        query: str,
        user_id: str,
        trace_id: str | None = None,
    ) -> SQLResult:
        # Cache key excluye user_id: el mismo texto genera el mismo SQL
        # independientemente de quién pregunta — el SQL es determinístico por query
        cache_key = hashlib.md5(query.strip().lower().encode()).hexdigest()

        # _traced: self._redis.get es llamada a cliente externo (redis-py)
        cached = self._traced("cache-check", lambda: self._redis.get(cache_key))
        if cached:
            sql_output = SQLOutput.model_validate_json(cached)
            # _traced: QueryRepository vive en otra capa (repositories)
            rows = self._traced(
                "sql-execution",
                lambda: self._query_repository.execute_sql(sql_output.sql),
                inputs={"sql": sql_output.sql},
                outputs_fn=lambda r: {"row_count": len(r)},
            )
            return SQLResult(
                sql=sql_output.sql,
                confidence=sql_output.confidence,
                tables_used=sql_output.tables_used,
                detected_language=sql_output.detected_language,
                response_hint=sql_output.response_hint,
                results=rows,
                row_count=len(rows),
            )

        # _traced: EmbeddingService vive en otra capa (services pero externo a este módulo)
        self._traced("embedding", lambda: self._embedding_service.embed(query))

        # _traced: SchemaRepository vive en otra capa (repositories)
        relevant_tables = self._traced(
            "rag-retrieval",
            lambda: self._schema_repository.find_relevant_tables(query),
            inputs={"query": query},
            outputs_fn=lambda tables: {
                "chunk_count": len(tables),
                "table_names": [t.get("table_name") for t in tables],
            },
        )
        schema_context = "\n\n".join(t["schema_text"] for t in relevant_tables)

        # Nombres reales de tablas SQL (sin prefijos de documentos pgvector)
        valid_sql_tables = self._schema_repository.get_valid_sql_tables()

        sql_output: SQLOutput = self._chain.run(
            query=query, schema_context=schema_context, trace_id=trace_id
        )

        guardrails = GuardrailFactory.get_all(valid_tables=valid_sql_tables)
        for guardrail in guardrails:
            # _traced: nombre dinámico (guardrail-{ClassName}) — @traceable
            # requiere nombre estático en decoración. Además Guardrail vive
            # en otra capa.
            name = type(guardrail).__name__
            result = self._traced(
                f"guardrail-{name}",
                lambda g=guardrail: g.validate(sql_output),
                inputs={"sql": sql_output.sql, "tables_used": sql_output.tables_used},
                outputs_fn=lambda r: {"blocked": r.blocked, "reason": r.reason},
            )
            if result.blocked:
                self._save_history(
                    user_id, query, sql_output, was_blocked=True, block_reason=result.reason
                )
                raise QueryBlockedError(result.reason)

        # Solo cacheamos después de pasar guardrails — no cacheamos SQL bloqueado
        self._redis.setex(cache_key, 3600, sql_output.model_dump_json())

        # _traced: QueryRepository vive en otra capa (repositories)
        rows = self._traced(
            "sql-execution",
            lambda: self._query_repository.execute_sql(sql_output.sql),
            inputs={"sql": sql_output.sql},
            outputs_fn=lambda r: {"row_count": len(r)},
        )
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
