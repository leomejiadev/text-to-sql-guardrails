import os

from google import genai


class EmbeddingService:
    def __init__(self, api_key: str = None, model: str = None):
        # gemini-embedding-001 produce vectores de 768 dims (acoplado al schema pgvector)
        self._model = model or os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
        self._client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))

    def embed(self, text: str) -> list[float]:
        if not text:
            raise ValueError("El texto no puede ser vacío para generar un embedding")

        # embed_content retorna EmbedContentResponse; .embeddings[0].values es list[float]
        response = self._client.models.embed_content(model=self._model, contents=text)
        return list(response.embeddings[0].values)
