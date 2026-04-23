"""
Repository responsable de ejecutar SQL validado contra la DB
relacional del cliente. Solo lectura — nunca escribe datos.
Desacoplado del resto del sistema: si cambia la DB del cliente,
solo cambia este archivo.
"""
import os

from sqlalchemy import create_engine, text


class QueryRepository:
    def __init__(self, engine=None, db_url: str = None):
        # engine se acepta directamente para facilitar el mocking en tests unitarios
        if engine is not None:
            self._engine = engine
        else:
            url = db_url or os.getenv("CLIENT_DATABASE_URL")
            self._engine = create_engine(url)

    def execute_sql(self, sql: str) -> list[dict]:
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(sql))
                # RowMapping → dict estándar para desacoplar la respuesta de SQLAlchemy
                return [dict(row._mapping) for row in result]
        except Exception as exc:
            raise RuntimeError(f"Error al ejecutar SQL: {exc}") from exc

    def get_schema(self) -> dict[str, str]:
        query = text("""
            SELECT
                t.table_name,
                string_agg(
                    c.column_name || ' ' || c.data_type,
                    ', ' ORDER BY c.ordinal_position
                ) AS columns
            FROM information_schema.tables AS t
            JOIN information_schema.columns AS c
                ON  t.table_name  = c.table_name
                AND t.table_schema = c.table_schema
            WHERE t.table_schema = 'public'
              AND t.table_type   = 'BASE TABLE'
            GROUP BY t.table_name
            ORDER BY t.table_name
        """)
        with self._engine.connect() as conn:
            rows = conn.execute(query)
            # Descripción en lenguaje natural para que el embedding capture el significado
            return {
                row.table_name: f"Tabla '{row.table_name}', columnas: {row.columns}"
                for row in rows
            }
