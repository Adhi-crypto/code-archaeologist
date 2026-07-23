from pydantic import BaseModel
from typing import Any, Optional

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class IngestionStatus(BaseModel):
    repo_id: str
    status: str
    progress: int
    total: int
    message: str