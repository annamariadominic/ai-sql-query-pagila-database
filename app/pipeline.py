from app.db import get_schema_context, run_sql
from app.llm import generate_sql, summarize_results
from app.logging_utils import get_logger
from app.sql_safety import clean_sql, is_safe_sql, extract_tables_from_sql

logger = get_logger(__name__)


def run_query_pipeline(question: str) -> dict:
    logger.info(f"Starting pipeline for question: {question}")

    schema_context = get_schema_context()
    raw_sql = generate_sql(question, schema_context)
    sql = clean_sql(raw_sql)

    is_safe, reason = is_safe_sql(sql)
    if not is_safe:
        logger.error(f"Unsafe SQL rejected: {reason}")
        raise ValueError(f"Unsafe SQL rejected: {reason}")

    tables_used = extract_tables_from_sql(sql)
    logger.info(f"Tables used in SQL: {tables_used}")

    rows = run_sql(sql)

    analysis = None
    lowered = question.lower()
    if any(keyword in lowered for keyword in ["analyze", "trend", "over time", "fair", "determine"]):
        analysis = summarize_results(question, sql, rows)

    response = {
        "question": question,
        "generated_sql": sql,
        "rows": rows,
        "analysis": analysis,
        "trace": {
            "row_count": len(rows),
            "analysis_performed": analysis is not None,
            "sql_validated": True,
            "tables_used": tables_used,
            "schema_context_type": "static_v1",
        },
    }

    logger.info(f"Pipeline complete for question: {question}")
    return response
