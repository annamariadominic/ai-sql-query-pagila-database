from fastapi import FastAPI, HTTPException
from app.logging_utils import get_logger
from app.pipeline import run_query_pipeline
from app.schemas import QueryRequest, QueryResponse

logger = get_logger(__name__)

app = FastAPI(title="Tetrix Take-Home Query API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_database(request: QueryRequest):
    try:
        result = run_query_pipeline(request.question)
        return result
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=400, detail=str(e))