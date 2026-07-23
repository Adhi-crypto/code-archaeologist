from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from app.reasoning.bug_origin_analyzer import analyze_bug_origin
from app.ingestion.git_ingestor import get_repo_id

router = APIRouter()


class BugOriginRequest(BaseModel):
    repo_id: str
    query: str
    repo_name: str = "Repository"


@router.post("/bug-origin", response_model=dict)
@router.post("/bug-origin/analyze", response_model=dict)
async def analyze_bug(request: BugOriginRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        result = await analyze_bug_origin(
            repo_id=request.repo_id,
            query=request.query,
            repo_name=request.repo_name,
        )
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bug origin analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
