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
    Naive but useful extraction of tables referenced in FROM and JOIN clauses.
    """
    sql_clean = clean_sql(sql)

    pattern = r'\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
    matches = re.findall(pattern, sql_clean, flags=re.IGNORECASE)

    seen = []
    for table in matches:
        table_lower = table.lower()
        if table_lower not in seen:
            seen.append(table_lower)

    return seen