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
    lines = [line.strip() for line in sql_clean.splitlines() if line.strip()]

    matches = []
    for line in lines:
        lower = line.lower()
        if lower.startswith("from ") or lower.startswith("join "):
            parts = line.split()
            if len(parts) >= 2:
                table = parts[1].strip(",")
                matches.append(table.lower())

    seen = []
    for table in matches:
        if table not in seen:
            seen.append(table)

    return seen