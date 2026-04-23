"""Fixtures compartidas para toda la suite de integración.

Nivel: tests/ (raíz). Los conftest.py más cercanos (tests/integration/)
tienen precedencia sobre estos para tests dentro de esa carpeta.
"""
import os

import pytest
import redis
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlmodel import SQLModel

load_dotenv()

# Importar todos los modelos para que SQLModel.metadata los registre
# antes de create_all — sin este import las tablas no se crean.
import app.models.query_history  # noqa: F401


# scope="session": las tablas se crean UNA SOLA VEZ para toda la suite.
# scope="function" recrearía el schema en cada test — costoso con pgvector y
# extensiones custom. El rollback al final de la sesión limpia todo.
@pytest.fixture(scope="session")
def db_session():
    """Engine + Session apuntando a TEST_DATABASE_URL, tablas creadas una vez."""
    db_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5433/test_text_to_sql",
    )
    engine = create_engine(db_url)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Savepoint al inicio: el rollback al final limpia todos los datos
        # insertados durante la sesión de tests sin destruir las tablas.
        session.begin_nested()
        yield session
        session.rollback()

    SQLModel.metadata.drop_all(engine)


# scope="session": una sola conexión Redis para toda la suite.
# scope="function" abriría y cerraría la conexión en cada test — overhead
# innecesario cuando el cliente Redis es thread-safe y reutilizable.
@pytest.fixture(scope="session")
def redis_client():
    """Cliente Redis conectado a REDIS_URL, reutilizado en todos los tests."""
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client = redis.from_url(url, decode_responses=True)
    yield client
    client.close()


# scope="session": la app FastAPI y su lifespan se inicializan UNA sola vez.
# scope="function" re-ejecutaría el startup de FastAPI (conexiones, Limiter)
# en cada test — lento e innecesario para una app stateless.
@pytest.fixture(scope="session")
def app_client():
    """TestClient de FastAPI, session-scoped para evitar re-inicializar la app."""
    from app.main import app

    with TestClient(app) as client:
        yield client
