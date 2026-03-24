from openai import OpenAI
from app.config import settings
from app.logging_utils import get_logger

logger = get_logger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_sql(question: str, schema_context: str) -> str:
    logger.info(f"Generating SQL for question: {question}")

    prompt = f"""
You are an expert PostgreSQL analyst.

Given the database schema context below, write a SQL query that answers the user's question.

Schema context:
{schema_context}

Rules:
- Use PostgreSQL syntax.
- Return ONLY the SQL query.
- Use explicit JOINs.
- Do not include markdown fences.
- Only generate a read-only query.
- If the question asks for highest and lowest, you may use ORDER BY and LIMIT or CTEs.
- If the user asks for analysis over time, return the aggregated data needed for analysis.

User question:
{question}
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You write safe, accurate PostgreSQL queries."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    sql = response.choices[0].message.content.strip()
    logger.info(f"Generated SQL: {sql}")
    return sql


def summarize_results(question: str, sql: str, rows: list[dict]) -> str:
    logger.info("Summarizing query results")

    if not rows:
        return "No results found."

    prompt = f"""
You are a data analyst.

The user asked:
{question}

The SQL used was:
{sql}

The query results are:
{rows}

Write a concise, accurate summary of the results.
If the question asks for a trend or analysis, explain the pattern based only on the results shown.
Do not invent facts.
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You summarize SQL results faithfully."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    summary = response.choices[0].message.content.strip()
    logger.info(f"Generated summary: {summary}")
    return summary