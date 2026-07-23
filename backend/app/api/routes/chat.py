from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.reasoning.causal_reasoner import answer_repo_question, explain_causal

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