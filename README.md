# AI-Powered PostgreSQL Query & Analysis API

A FastAPI-based system that converts natural language questions into safe PostgreSQL queries, executes them against the Pagila database, and optionally generates analytical summaries.

---

## Overview

This system enables users to ask analytical questions over a relational database using natural language. It dynamically inspects the database schema, generates SQL queries using an LLM, validates them for safety, executes them, and returns structured results along with trace metadata for observability.

---

## Features

- Natural language → SQL query generation
- Dynamic schema introspection from PostgreSQL
- Read-only SQL validation for safety
- Query execution with structured results
- Optional analytical summarization
- Observability via trace metadata and logs
- Lightweight SQL repair loop for failed queries

---

## Architecture

```text
User Question
    ↓
Dynamic Schema Introspection
    ↓
LLM SQL Generation
    ↓
SQL Validation (read-only enforcement)
    ↓
SQL Execution (PostgreSQL)
    ↓
Optional Analysis (LLM)
    ↓
Response + Trace Metadata
```

---


### Key Components

- `app/db.py`  
  Handles database connection, schema introspection, and query execution  

- `app/llm.py`  
  Responsible for SQL generation, SQL repair, and result summarization  

- `app/pipeline.py`  
  Orchestrates the full query pipeline  

- `app/sql_safety.py`  
  Validates SQL queries and extracts tables used  

- `app/main.py`  
  FastAPI application entry point  

---

## Design Decisions

- **Text-to-SQL over RAG**  
  Since the data is structured and stored in PostgreSQL, direct SQL generation is more appropriate than document retrieval.

- **Dynamic schema introspection**  
  The system queries the live database schema at runtime, ensuring queries are grounded in the actual structure.

- **Schema-aware prompting (with data types)**  
  Column data types are included in schema context to reduce incorrect usage of functions (e.g., date functions on integer fields).

- **Read-only SQL enforcement**  
  Only SELECT queries are allowed to prevent unintended modifications.

- **Observability-first design**  
  Each request returns detailed trace metadata, including execution timing, tables used, and validation status.

- **Single-pass generation with repair loop**  
  The system generates SQL once and attempts a single repair if execution fails.

---

## Observability & Traceability

Each response includes a `trace` object with:

- `tables_used` → Tables referenced in the query  
- `schema_tables_available` → Tables available in schema context  
- `sql_execution_time_ms` → Query execution latency  
- `total_pipeline_time_ms` → End-to-end latency  
- `analysis_performed` → Whether summarization was triggered  
- `repair_attempted` / `repair_succeeded` → Repair loop status  
- `sql_validated` → Whether query passed safety checks  

Additionally, logs are written to:
- Console  
- `logs/app.log`  

---

## Limitations

- The system may return a **proxy metric** if a concept does not exist in the schema.  
  Example: “box office revenue” may be approximated using rental payment data.

- SQL repair loop is **single-pass** and not fully robust to complex failures.

- Analysis triggering uses **keyword matching** instead of full intent classification.

- Schema context includes all tables; future work could include **table selection/query planning**.

- No automated evaluation suite was implemented due to time constraints.

---

## Setup Instructions

### Prerequisites

- Python 3.9+  
- PostgreSQL installed locally  
- Pagila dataset loaded into PostgreSQL  
- OpenAI API key  

---

### 1. Create Virtual Environment

```bash
python3 -m venv virtual
source virtual/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a .env file:

```bash
OPENAI_API_KEY=your_api_key_here

DB_HOST=localhost
DB_PORT=5432
DB_NAME=pagila
DB_USER=your_db_user
DB_PASSWORD=

OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

### 4. Load Pagila Database

```bash
createdb pagila
psql -d pagila -f pagila-schema.sql
psql -d pagila -f pagila-data.sql
```

### 5. Run the Application

```bash
python run.py
```

### 6. Access the API Docs

Go to http://127.0.0.1:8000/docs in your local browser

---

## Example Queries

### Simple Query

```json
{
  "question": "List 5 film titles"
}
```

### Join Query

```json
{
  "question": "What actors were in the film ACADEMY DINOSAUR?"
}
```

### Aggregation Query

```json
{
  "question": "Display the top 3 actors who have most appeared in films in the Children category"
}
```

### Analytical Query

```json
{
  "question": "Analyze film lengths over time and determine if they are increasing"
}
```

---

## Future Improvements

- Semantic validation layer for unsupported concepts
- Improved SQL repair with structured parsing
- Query planning / table selection to reduce prompt size
- Automated evaluation framework for NL → SQL accuracy
- Result caching for repeated queries

---

## Notes

This project focuses on building a trustworthy, observable, and schema-aware data retrieval system, rather than just generating SQL queries. The emphasis is on correctness, traceability, and clear system behavior.

---