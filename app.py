"""
FastAPI application for Natural Language to SQL translation
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from nlp_to_sql import NLToSQLTranslator
from config import settings

app = FastAPI(
    title="Natural Language to SQL Translator",
    description="LLM-powered SQL generator with schema-aware prompting and query validation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize translator
translator = NLToSQLTranslator(settings.DATABASE_PATH)


class QueryRequest(BaseModel):
    """Request model for natural language query"""
    query: str
    use_cache: bool = True


class QueryResponse(BaseModel):
    """Response model for SQL query"""
    sql: str
    explanation: Optional[str] = None
    cached: bool = False
    execution_time: Optional[float] = None


class ExecuteRequest(BaseModel):
    """Request model for executing SQL query"""
    sql: str
    limit: int = 100


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Natural Language to SQL Translator",
        "version": "1.0.0"
    }


@app.get("/schema")
async def get_schema():
    """Get database schema information"""
    try:
        schema = translator.get_schema()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate", response_model=QueryResponse)
async def translate_query(request: QueryRequest):
    """
    Translate natural language query to SQL
    """
    try:
        result = translator.translate(
            natural_language_query=request.query,
            use_cache=request.use_cache
        )
        
        return QueryResponse(
            sql=result["sql"],
            explanation=result.get("explanation"),
            cached=result.get("cached", False),
            execution_time=result.get("execution_time")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute")
async def execute_query(request: ExecuteRequest):
    """
    Execute SQL query and return results
    """
    try:
        # Validate query safety
        if not translator.validator.is_safe(request.sql):
            raise HTTPException(
                status_code=400,
                detail="Query contains potentially unsafe operations"
            )
        
        results = translator.execute_query(request.sql, limit=request.limit)
        return {
            "results": results["data"],
            "row_count": results["row_count"],
            "columns": results["columns"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_and_execute(request: QueryRequest):
    """
    Translate natural language to SQL and execute it in one step
    """
    try:
        # Translate
        translation_result = translator.translate(
            natural_language_query=request.query,
            use_cache=request.use_cache
        )
        
        # Execute
        execution_result = translator.execute_query(
            translation_result["sql"],
            limit=100
        )
        
        return {
            "sql": translation_result["sql"],
            "explanation": translation_result.get("explanation"),
            "cached": translation_result.get("cached", False),
            "execution_time": translation_result.get("execution_time"),
            "results": execution_result["data"],
            "row_count": execution_result["row_count"],
            "columns": execution_result["columns"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

