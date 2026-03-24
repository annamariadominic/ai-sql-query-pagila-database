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


def get_schema_context() -> str:
    """
    Keep this concise and useful.
    """
    schema_context = """
You are querying a PostgreSQL pagila database.

Key tables:
- film(film_id, title, description, release_year, language_id, rental_duration, rental_rate, length, rating)
- actor(actor_id, first_name, last_name)
- film_actor(actor_id, film_id)
- category(category_id, name)
- film_category(film_id, category_id)
- customer(customer_id, store_id, first_name, last_name, email, address_id, activebool, create_date)
- inventory(inventory_id, film_id, store_id)
- rental(rental_id, rental_date, inventory_id, customer_id, return_date, staff_id)
- payment(payment_id, customer_id, staff_id, rental_id, amount, payment_date)

Important relationships:
- film_actor links films and actors
- film_category links films and categories
- inventory links films to rentable copies
- rental links customers to inventory
- payment links customers and rentals to payments

Notes:
- Use PostgreSQL syntax.
- Prefer explicit JOINs.
- Return only a read-only SQL query.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
"""
    logger.info("Loaded schema context")
    return schema_context