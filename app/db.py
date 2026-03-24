from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import settings
from app.logging_utils import get_logger

logger = get_logger(__name__)


def get_connection():
    logger.info(
        f"Connecting to DB host={settings.DB_HOST} port={settings.DB_PORT} db={settings.DB_NAME} user={settings.DB_USER}"
    )
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )


def run_sql(sql: str) -> list[dict[str, Any]]:
    logger.info(f"Executing SQL: {sql}")
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            logger.info(f"Query returned {len(rows)} rows")
            return [dict(row) for row in rows]


def get_schema_metadata() -> dict:
    """
    Dynamically fetch key table/column metadata and foreign key relationships
    from the public schema.
    """
    allowed_tables = {
        "film",
        "actor",
        "film_actor",
        "category",
        "film_category",
        "customer",
        "inventory",
        "rental",
        "payment",
        "language",
        "store",
        "staff",
        "address",
        "city",
        "country",
    }

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT table_name, column_name, ordinal_position
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
                """
            )
            column_rows = cur.fetchall()

            cur.execute(
                """
                SELECT
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public';
                """
            )
            fk_rows = cur.fetchall()

    tables: dict[str, list[str]] = {}
    for row in column_rows:
        table_name = row["table_name"]
        if table_name not in allowed_tables:
            continue
        tables.setdefault(table_name, []).append(row["column_name"])

    foreign_keys = []
    for row in fk_rows:
        if row["table_name"] in allowed_tables and row["foreign_table_name"] in allowed_tables:
            foreign_keys.append(
                {
                    "table_name": row["table_name"],
                    "column_name": row["column_name"],
                    "foreign_table_name": row["foreign_table_name"],
                    "foreign_column_name": row["foreign_column_name"],
                }
            )

    metadata = {
        "tables": tables,
        "foreign_keys": foreign_keys,
    }

    logger.info(
        f"Loaded dynamic schema metadata for {len(tables)} tables and {len(foreign_keys)} foreign keys"
    )
    return metadata


def get_schema_context() -> tuple[str, list[str]]:
    """
    Build a concise schema context string dynamically from Postgres metadata.
    Returns:
      - schema context string
      - list of schema tables included
    """
    metadata = get_schema_metadata()
    tables = metadata["tables"]
    foreign_keys = metadata["foreign_keys"]

    lines = ["You are querying a PostgreSQL database.", "", "Relevant tables and columns:"]
    schema_tables_available = sorted(tables.keys())

    for table_name in schema_tables_available:
        columns = ", ".join(tables[table_name])
        lines.append(f"- {table_name}({columns})")

    lines.append("")
    lines.append("Important foreign key relationships:")
    for fk in foreign_keys:
        lines.append(
            f"- {fk['table_name']}.{fk['column_name']} -> "
            f"{fk['foreign_table_name']}.{fk['foreign_column_name']}"
        )

    lines.append("")
    lines.append("Rules:")
    lines.append("- Use PostgreSQL syntax.")
    lines.append("- Prefer explicit JOINs.")
    lines.append("- Return only a read-only SQL query.")
    lines.append("- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.")

    schema_context = "\n".join(lines)
    logger.info("Built dynamic schema context")

    return schema_context, schema_tables_available