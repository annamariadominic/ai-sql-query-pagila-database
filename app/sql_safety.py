import re


FORBIDDEN_KEYWORDS = [
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
]


def clean_sql(sql: str) -> str:
    sql = sql.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


def is_safe_sql(sql: str) -> tuple[bool, str]:
    sql_clean = clean_sql(sql)
    lowered = sql_clean.lower()

    if any(keyword in lowered for keyword in FORBIDDEN_KEYWORDS):
        return False, "SQL contains forbidden keywords"

    if ";" in sql_clean[:-1]:
        return False, "Multiple SQL statements are not allowed"

    if not (lowered.startswith("select") or lowered.startswith("with")):
        return False, "Only SELECT or WITH queries are allowed"

    return True, ""

def extract_tables_from_sql(sql: str) -> list[str]:
    """
    Naive but useful pragmatic extraction of tables referenced in FROM and JOIN clauses.
    Avoids false positives like EXTRACT(YEAR FROM ...).
    """
    sql_clean = clean_sql(sql)
    tokens = sql_clean.replace("\n", " ").split()

    tables = []
    for i, token in enumerate(tokens):
        token_lower = token.lower()

        if token_lower in ("from", "join"):
            if i + 1 < len(tokens):
                table = tokens[i + 1].strip(",")
                table = table.split(".")[-1]  # remove schema if present
                tables.append(table.lower())

    seen = []
    for table in tables:
        if table not in seen:
            seen.append(table)

    return seen