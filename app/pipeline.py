from app.db import get_schema_context, run_sql
from app.llm import generate_sql, summarize_results, repair_sql
from app.logging_utils import get_logger
from app.sql_safety import clean_sql, is_safe_sql, extract_tables_from_sql
import time

logger = get_logger(__name__)

ANALYSIS_KEYWORDS = ["analyze", "analyse", "analysis", "trend", "over time", "fair", "determine"]


def run_query_pipeline(question: str) -> dict:
    pipeline_start = time.time()
    logger.info(f"Starting pipeline for question: {question}")

    schema_context, schema_tables_available = get_schema_context()
    raw_sql = generate_sql(question, schema_context)
    sql = clean_sql(raw_sql)

    is_safe, reason = is_safe_sql(sql)
    if not is_safe:
        logger.error(f"Unsafe SQL rejected: {reason}")
        raise ValueError(f"Unsafe SQL rejected: {reason}")

    tables_used = extract_tables_from_sql(sql)
    logger.info(f"Tables used in SQL: {tables_used}")

    sql_execution_start = time.time()
    repair_attempted = False
    repair_succeeded = False
    repair_error = None

    try:
        rows = run_sql(sql)
    except Exception as e:
        logger.exception("Initial SQL execution failed")
        repair_attempted = True
        repair_error = str(e)

        repaired_raw_sql = repair_sql(
            question=question,
            schema_context=schema_context,
            failed_sql=sql,
            error_message=repair_error,
        )
        repaired_sql = clean_sql(repaired_raw_sql)

        is_safe, reason = is_safe_sql(repaired_sql)
        if not is_safe:
            logger.error(f"Unsafe repaired SQL rejected: {reason}")
            raise ValueError(f"Unsafe repaired SQL rejected: {reason}")

        sql = repaired_sql
        tables_used = extract_tables_from_sql(sql)
        logger.info(f"Tables used in repaired SQL: {tables_used}")

        rows = run_sql(sql)
        repair_succeeded = True

    sql_execution_time_ms = round((time.time() - sql_execution_start) * 1000, 2)

    analysis = None
    analysis_triggered_by = None
    lowered = question.lower()

    if any(keyword in lowered for keyword in ANALYSIS_KEYWORDS):
        analysis = summarize_results(question, sql, rows)
        analysis_triggered_by = "keyword_match"

    total_pipeline_time_ms = round((time.time() - pipeline_start) * 1000, 2)

    response = {
        "question": question,
        "generated_sql": sql,
        "rows": rows,
        "analysis": analysis,
        "trace": {
            "row_count": len(rows),
            "analysis_performed": analysis is not None,
            "analysis_triggered_by": analysis_triggered_by,
            "sql_validated": True,
            "tables_used": tables_used,
            "schema_context_type": "dynamic_v1",
            "schema_tables_available": schema_tables_available,
            "sql_execution_time_ms": sql_execution_time_ms,
            "total_pipeline_time_ms": total_pipeline_time_ms,
            "repair_attempted": repair_attempted,
            "repair_succeeded": repair_succeeded,
            "repair_error": repair_error,
        },
    }

    logger.info(
        f"Pipeline complete for question: {question} | "
        f"sql_execution_time_ms={sql_execution_time_ms} | "
        f"total_pipeline_time_ms={total_pipeline_time_ms} | "
        f"repair_attempted={repair_attempted} | repair_succeeded={repair_succeeded}"
    )
    return response