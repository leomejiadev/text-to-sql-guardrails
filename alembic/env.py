"""Script de entorno de Alembic.

Responsabilidades:
  1. Leer la URL de DB desde la variable de entorno DATABASE_URL (no del .ini).
  2. Registrar el metadata de los modelos SQLModel como `target_metadata`
     para que `alembic revision --autogenerate` detecte cambios.
  3. Correr migraciones en modo online (con engine) u offline (SQL a stdout).

El proyecto usa asyncpg en runtime, pero Alembic corre en un proceso aparte
(en CI o previo al deploy), así que acá convertimos la URL a la variante
sync con psycopg2 — más simple que mantener un event loop solo para migrar.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

# Agregamos el root del proyecto al sys.path para que Alembic pueda
# importar el paquete `app`. Alembic se invoca como script aparte y no
# hereda el path que sí tiene el proceso de FastAPI.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic import context  # noqa: E402
from sqlalchemy import engine_from_config, pool  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

# Import obligatorio: al importar los modelos, SQLModel.metadata queda
# poblado con sus tablas — sin esto, autogenerate no detecta nada.
# noqa: F401 porque el import se hace por su side effect (registrar tabla).
from app.models.query_history import QueryHistory  # noqa: E402, F401

# Objeto de configuración de Alembic; expone las secciones del alembic.ini.
config = context.config

# Configura logging según el [loggers]/[handlers]/... del alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _resolve_database_url() -> str:
    """Obtiene la URL de DB desde el entorno y la normaliza a driver sync.

    En runtime usamos `postgresql+asyncpg://...` para FastAPI async, pero
    Alembic corre sync — usar asyncpg acá obliga a un async_engine_from_config
    y un event loop, complicación innecesaria para un script de migración.
    Reemplazamos el driver a psycopg2, que ya está en las deps del proyecto.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        # Fallar temprano con mensaje claro: una migración sin URL es un
        # error de configuración del operador, no algo que Alembic deba
        # resolver silenciosamente.
        raise RuntimeError(
            "DATABASE_URL no está definida; exportala antes de correr alembic"
        )
    # Normalización: asyncpg → psycopg2 para uso sync dentro de Alembic.
    return url.replace("+asyncpg", "+psycopg2")


# Registramos la URL ya resuelta en la config de Alembic — el resto del
# script la consume desde acá, sin volver a leer el entorno.
config.set_main_option("sqlalchemy.url", _resolve_database_url())

# Metadata que Alembic usa para autogenerate. SQLModel comparte el mismo
# MetaData de SQLAlchemy, así que apuntamos ahí directamente.
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline: emite SQL a stdout sin conectar.

    Útil para revisar qué SQL se va a correr en producción antes de
    ejecutarlo (p. ej. para auditoría o para DBAs que aplican manualmente).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        # render_as_batch=False: solo útil para SQLite; en Postgres no aplica.
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones contra una DB real — el caso normal."""
    # NullPool: cada invocación de Alembic abre una conexión y la cierra.
    # No queremos un pool persistente porque el script es de corta vida.
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Alembic decide el modo según cómo se lo invoque: `--sql` activa offline.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
