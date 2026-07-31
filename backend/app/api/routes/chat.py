from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
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
    if not request.repo_id.strip():
        raise HTTPException(status_code=400, detail="Repository ID is required")

    logger.info(f"[POST /api/chat/query] Mode: {request.mode} | Repo: {request.repo_id} | Query: '{request.query[:50]}'")

    try:
        if request.mode == "causal":
            result = await explain_causal(request.query, request.repo_id)
        else:
            result = await answer_repo_question(request.query, request.repo_id)

        return {"success": True, "data": result}
    except RuntimeError as e:
        logger.error(f"[API ERROR 503] Chat pipeline RuntimeError: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"[API ERROR 500] Unexpected exception in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal chat processing error: {type(e).__name__}: {str(e)}")