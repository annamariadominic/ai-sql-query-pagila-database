from typing import Any, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)


class QueryResponse(BaseModel):
    question: str
    generated_sql: str
    rows: list[dict[str, Any]]
    analysis: Optional[str] = None
    trace: dict[str, Any]