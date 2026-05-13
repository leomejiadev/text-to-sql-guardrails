"""Seedea la DB del cliente si está vacía.

Idempotente: si las tablas ya existen con datos, no hace nada.
Necesario en entornos cloud (AWS RDS, etc.) donde no hay bind mounts
para docker-entrypoint-initdb.d.
"""
import os
import sys

from sqlalchemy import create_engine, text

SEED_FILE = os.path.join(os.path.dirname(__file__), "..", "docker", "init_client", "seed_starbucks.sql")


def _client_db_is_empty(conn) -> bool:
    result = conn.execute(text("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    """))
    return result.scalar() == 0


def run() -> dict:
    """Ejecuta el seed y retorna el resultado. Importable desde el admin router."""
    url = os.getenv("CLIENT_DATABASE_URL")
    if not url:
        return {"seeded": False, "message": "CLIENT_DATABASE_URL no definida"}

    engine = create_engine(url)

    with engine.connect() as conn:
        if not _client_db_is_empty(conn):
            return {"seeded": False, "message": "DB del cliente ya tiene datos — seed omitido"}

    seed_path = os.path.abspath(SEED_FILE)
    if not os.path.exists(seed_path):
        raise FileNotFoundError(f"Archivo de seed no encontrado: {seed_path}")

    with open(seed_path) as f:
        sql = f.read()

    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()

    return {"seeded": True, "message": "Seed del cliente completado"}


if __name__ == "__main__":
    result = run()
    if not result["seeded"] and "no definida" in result["message"]:
        sys.exit(0)
    print(result["message"])
