#!/usr/bin/env python3
"""Verifica que el entorno está listo para deploy en contenedor.

Acumula todos los errores y los muestra juntos al final para que el operador
pueda corregir todos los problemas de una sola pasada, sin iterar check a check.
Sale con código 0 si todo pasa, código 1 con detalle si alguna verificación falla.
"""
import os
import sys


def _check_env_vars() -> list[str]:
    """Verifica que todas las variables de entorno requeridas están definidas."""
    required = [
        "DATABASE_URL",
        "REDIS_URL",
        "OPENAI_API_KEY",
        "SECRET_KEY",
        "REINDEX_INTERVAL_SECONDS",
    ]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        return [f"ENV: variables no definidas: {', '.join(missing)}"]
    return []


def _check_postgres() -> list[str]:
    """Verifica que Postgres responde con una query simple."""
    try:
        import sqlalchemy
        from sqlalchemy import create_engine, text

        url = os.getenv("DATABASE_URL", "")
        # asyncpg no soporta uso sincrónico en scripts — forzamos psycopg2
        sync_url = url.replace("+asyncpg", "+psycopg2")
        engine = create_engine(sync_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return []
    except Exception as exc:
        return [f"POSTGRES: no responde — {exc}"]


def _check_redis() -> list[str]:
    """Verifica que Redis responde con PING."""
    try:
        import redis

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(url, socket_connect_timeout=5)
        client.ping()
        client.close()
        return []
    except Exception as exc:
        return [f"REDIS: no responde — {exc}"]


def _check_alembic_migrations() -> list[str]:
    """Verifica que las migraciones están al día comparando revisión actual con head."""
    try:
        from alembic.config import Config
        from alembic.runtime.migration import MigrationContext
        from alembic.script import ScriptDirectory
        import sqlalchemy
        from sqlalchemy import create_engine

        url = os.getenv("DATABASE_URL", "")
        sync_url = url.replace("+asyncpg", "+psycopg2")

        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)

        # head puede ser múltiple en proyectos con branches de migración
        heads = set(script.get_heads())

        engine = create_engine(sync_url)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current = set(context.get_current_heads())

        if current != heads:
            return [
                f"ALEMBIC: migraciones desactualizadas — "
                f"actual={current or '(sin migrar)'}, head={heads}"
            ]
        return []
    except Exception as exc:
        return [f"ALEMBIC: error al verificar migraciones — {exc}"]


def main() -> None:
    errors: list[str] = []

    # Acumulamos todos los errores antes de imprimir para mostrarlos juntos
    errors.extend(_check_env_vars())
    errors.extend(_check_postgres())
    errors.extend(_check_redis())
    errors.extend(_check_alembic_migrations())

    if errors:
        print("❌ pre-deploy check FAILED:\n")
        for error in errors:
            print(f"  • {error}")
        sys.exit(1)

    print("✅ pre-deploy check passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
