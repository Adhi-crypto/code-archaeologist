from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.reasoning.evolution_detector import detect_evolution

router = APIRouter()

class EvolutionRequest(BaseModel):
    repo_id: str
    repo_name: str

@router.post("/analyze")
async def analyze_evolution(request: EvolutionRequest):
    try:
        result = await detect_evolution(request.repo_id, request.repo_name)
        return {"success": True, "data": result}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))