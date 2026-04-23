from app.repositories.query_repository import QueryRepository
from app.repositories.schema_repository import SchemaRepository


class IndexingService:
    def __init__(
        self,
        query_repository: QueryRepository,
        schema_repository: SchemaRepository,
    ):
        # Inyección de dependencias: el servicio no sabe de qué DB ni de qué vector store
        self._query_repo = query_repository
        self._schema_repo = schema_repository

    def reindex(self) -> dict:
        schemas = self._query_repo.get_schema()
        self._schema_repo.reindex_all(schemas)
        return {"reindexed_tables": len(schemas), "status": "success"}
