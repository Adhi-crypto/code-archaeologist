from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.reasoning.causal_reasoner import (
    answer_repo_question,
    explain_causal,
    answer_repo_question_stream,
)

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    repo_id: str
    mode: str = "chat"  # "chat" or "causal"

@router.post("/query")
async def query_repo(request: ChatRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        if request.mode == "causal":
            result = await explain_causal(request.query, request.repo_id)
        else:
            result = await answer_repo_question(request.query, request.repo_id)
        return {"success": True, "data": result}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.post("/query-stream")
async def query_repo_stream(request: ChatRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        generator = answer_repo_question_stream(
            query=request.query,
            repo_id=request.repo_id,
            mode=request.mode,
        )
        return StreamingResponse(generator, media_type="text/event-stream")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))