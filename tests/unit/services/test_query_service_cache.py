"""Tests para el cache Redis en QueryService.process()."""
import hashlib
from unittest.mock import MagicMock, patch


def _make_service(mock_chain, mock_redis):
    """Helper: construye QueryService con todas las deps mockeadas."""
    from app.services.query_service import QueryService

    service = QueryService(
        embedding_service=MagicMock(),
        schema_repository=MagicMock(),
        query_repository=MagicMock(),
        chain=mock_chain,
        session=MagicMock(),
    )
    service._redis = mock_redis
    return service


class TestQueryServiceCache:

    def test_cache_hit_returns_sql_output_without_calling_llm(self):
        """Cache hit debe retornar SQLOutput cacheado sin invocar el LLM."""
        from app.schemas.sql_output import SQLOutput

        cached = SQLOutput(
            sql="SELECT 1",
            detected_language="en",
            confidence="high",
            tables_used=["users"],
            response_hint="Lista de usuarios",
        )
        mock_redis = MagicMock()
        mock_redis.get.return_value = cached.model_dump_json()
        mock_chain = MagicMock()

        service = _make_service(mock_chain, mock_redis)
        result = service.process("show users", "user-1")

        assert result.sql == "SELECT 1"
        mock_chain.run.assert_not_called()

    def test_cache_miss_calls_llm_and_saves_to_redis(self):
        """Cache miss debe llamar al LLM y guardar el resultado con TTL=3600."""
        from app.schemas.sql_output import SQLOutput
        from app.guardrails.factory import GuardrailFactory

        sql_out = SQLOutput(
            sql="SELECT * FROM users",
            detected_language="en",
            confidence="high",
            tables_used=["users"],
            response_hint="Lista de usuarios",
        )
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_chain = MagicMock()
        mock_chain.run.return_value = sql_out

        with patch.object(GuardrailFactory, "get_all", return_value=[]):
            service = _make_service(mock_chain, mock_redis)
            service._schema_repository.find_relevant_tables.return_value = ["users"]
            result = service.process("show all users", "user-1")

        mock_chain.run.assert_called_once()
        mock_redis.setex.assert_called_once()
        _, ttl, _ = mock_redis.setex.call_args.args
        assert ttl == 3600
        assert result.sql == "SELECT * FROM users"

    def test_cache_key_is_md5_of_normalized_query_without_user_id(self):
        """Cache key debe ser MD5(query.strip().lower()) — sin user_id."""
        from app.schemas.sql_output import SQLOutput
        from app.guardrails.factory import GuardrailFactory

        query = "  Show ALL Users  "
        expected_key = hashlib.md5(query.strip().lower().encode()).hexdigest()

        sql_out = SQLOutput(
            sql="SELECT * FROM users",
            detected_language="en",
            confidence="high",
            tables_used=["users"],
            response_hint="Lista de usuarios",
        )
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_chain = MagicMock()
        mock_chain.run.return_value = sql_out

        with patch.object(GuardrailFactory, "get_all", return_value=[]):
            service = _make_service(mock_chain, mock_redis)
            service._schema_repository.find_relevant_tables.return_value = ["users"]
            service.process(query, "user-diferente")

        actual_key = mock_redis.get.call_args.args[0]
        assert actual_key == expected_key
