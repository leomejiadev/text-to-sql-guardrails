"""Tests unitarios para EmbeddingService — sin llamadas reales a Gemini."""
import pytest
from unittest.mock import MagicMock, patch


def test_embed_returns_list_of_floats():
    """Verifica que embed() retorna una lista de floats."""
    mock_client = MagicMock()
    mock_client.models.embed_content.return_value.embeddings = [
        MagicMock(values=[0.1, 0.2, 0.3])
    ]

    with patch("app.services.embedding_service.genai.Client", return_value=mock_client):
        from app.services.embedding_service import EmbeddingService
        service = EmbeddingService(api_key="test-key")
        result = service.embed("hello world")

    assert isinstance(result, list)
    assert all(isinstance(x, float) for x in result)


def test_embed_raises_value_error_on_empty_string():
    """Verifica que embed("") lanza ValueError antes de llamar a la API."""
    from app.services.embedding_service import EmbeddingService

    # genai.Client() no hace llamadas de red al instanciarse — no requiere mock
    service = EmbeddingService(api_key="test-key")
    with pytest.raises(ValueError):
        service.embed("")


def test_embed_calls_correct_model():
    """Verifica que embed() usa el modelo configurado en el constructor."""
    mock_client = MagicMock()
    mock_client.models.embed_content.return_value.embeddings = [
        MagicMock(values=[0.1, 0.2, 0.3])
    ]

    with patch("app.services.embedding_service.genai.Client", return_value=mock_client):
        from app.services.embedding_service import EmbeddingService
        service = EmbeddingService(api_key="test-key", model="text-embedding-004")
        service.embed("hello world")

        mock_client.models.embed_content.assert_called_once_with(
            model="text-embedding-004",
            contents="hello world",
        )
