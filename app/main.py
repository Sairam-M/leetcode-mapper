from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
from app.models import ProblemResponse, ProblemRequest, ReasoningOutput
from app.search import search_similar_problems
from app.reasoning import generate_reasoning

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import faiss
import pandas as pd


@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs once on startup
    app.state.index = faiss.read_index("./data/leetcode.index")
    app.state.df = pd.read_csv("./data/leetcode_clean.csv")
    
    yield  # app is running, handling requests
    
    # runs once on shutdown
    # cleanup if needed

app = FastAPI(lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/health")
def health_check():
    return {"status": "healthy", 
            "index_loaded": app.state.index is not None,
            "df_loaded": app.state.df is not None}


@app.post("/leetcode-equivalent", response_model=ProblemResponse)
@limiter.limit("5/minute")
def search_leetcode_equivalent(request: Request, problem_statement: ProblemRequest):
    index = app.state.index
    df = app.state.df
    
    normalized_problem, distances, indices = search_similar_problems(problem_statement.problem_statement, index)
    reasoning_result = generate_reasoning(problem_statement.problem_statement, normalized_problem, df, indices)

    if not reasoning_result.get('leetcode_title'):
        raise HTTPException(status_code=500, detail="Could not find a matching problem")

    return ProblemResponse(
        leetcode_title=reasoning_result['leetcode_title'],
        leetcode_link=reasoning_result['leetcode_link'],
        difficulty=reasoning_result['difficulty'],
        acceptance_rate=reasoning_result['acceptance_rate'],
        topics=reasoning_result['topics'],
        reasoning=ReasoningOutput(
            pattern=reasoning_result.get('pattern', ''),
            core_constraint=reasoning_result.get('core_constraint', ''),
            why_it_matches=reasoning_result.get('why_it_matches', ''),
            key_difference=reasoning_result.get('key_difference', ''),
            confidence=reasoning_result.get('confidence', '')
        )
    )