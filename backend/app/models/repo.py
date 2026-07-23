from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class RepoIngestionRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    max_commits: int = 500
    include_prs: bool = True
    include_issues: bool = True

class CommitRecord(BaseModel):
    sha: str
    message: str
    author: str
    timestamp: datetime
    files_changed: list[str]
    additions: int
    deletions: int
    diff_summary: str = ""

class RepoMetadata(BaseModel):
    repo_id: str
    repo_url: str
    repo_name: str
    branch: str
    total_commits: int
    languages: list[str]
    ingested_at: datetime
    status: str = "pending"