"""Fixtures para tests de integración — requieren PostgreSQL + pgvector corriendo."""
import os

import pytest
from dotenv import load_dotenv

# Cargar .env antes de que cualquier fixture acceda a variables de entorno
load_dotenv()
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


@pytest.fixture(scope="session")
def test_engine():
    """Engine conectado a la DB de tests (TEST_DATABASE_URL)."""
    db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5433/test_text_to_sql",
    )
    engine = create_engine(db_url)

    # Crear extensión y tabla antes de correr los tests
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_embeddings (
                id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
                table_name  VARCHAR UNIQUE NOT NULL,
                schema_text TEXT    NOT NULL,
                embedding   vector(3072) NOT NULL,
                created_at  TIMESTAMP DEFAULT now(),
                updated_at  TIMESTAMP DEFAULT now()
            )
        """))
        conn.commit()

    yield engine

    # Limpieza al final de la sesión de tests
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS schema_embeddings"))
        conn.commit()


@pytest.fixture
def db_session(test_engine):
    """Session que hace rollback automático al finalizar cada test."""
    with Session(test_engine) as session:
        yield session
        # Rollback garantiza aislamiento: cada test parte con tabla limpia
        session.rollback()


@pytest.fixture(scope="session")
def embedding_service():
    """EmbeddingService real — requiere GEMINI_API_KEY en el entorno."""
    from app.services.embedding_service import EmbeddingService

    return EmbeddingService()
