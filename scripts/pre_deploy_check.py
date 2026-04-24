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
        "CLIENT_DATABASE_URL",
        "REDIS_URL",
        "GEMINI_API_KEY",
        "SECRET_KEY",
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


def _check_postgres_client() -> list[str]:
    """Verifica que la DB del cliente responde."""
    try:
        from sqlalchemy import create_engine, text

        url = os.getenv("CLIENT_DATABASE_URL", "")
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return []
    except Exception as exc:
        return [f"POSTGRES_CLIENT: no responde — {exc}"]


def main() -> None:
    errors: list[str] = []

    # Acumulamos todos los errores antes de imprimir para mostrarlos juntos
    errors.extend(_check_env_vars())
    errors.extend(_check_postgres())
    errors.extend(_check_postgres_client())
    errors.extend(_check_redis())

    if errors:
        print("❌ pre-deploy check FAILED:\n")
        for error in errors:
            print(f"  • {error}")
        sys.exit(1)

    print("✅ pre-deploy check passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
