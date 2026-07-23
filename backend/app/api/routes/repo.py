from fastapi import APIRouter, HTTPException, BackgroundTasks
from loguru import logger
from app.models.repo import RepoIngestionRequest, RepoMetadata
from app.models.response import APIResponse, IngestionStatus
from app.ingestion.git_ingestor import ingest_repo, get_repo_id

router = APIRouter()

# In-memory status tracker (good enough for now)
ingestion_status: dict[str, IngestionStatus] = {}


@router.post("/ingest", response_model=APIResponse)
async def ingest_repository(request: RepoIngestionRequest, background_tasks: BackgroundTasks):
    repo_id = get_repo_id(request.repo_url)
    ingestion_status[repo_id] = IngestionStatus(
        repo_id=repo_id,
        status="running",
        progress=0,
        total=request.max_commits,
        message="Starting ingestion...",
    )
    background_tasks.add_task(_run_ingestion, request)
    return APIResponse(success=True, message="Ingestion started", data={"repo_id": repo_id})


@router.get("/status/{repo_id}", response_model=IngestionStatus)
async def get_ingestion_status(repo_id: str):
    if repo_id not in ingestion_status:
        raise HTTPException(status_code=404, detail="Repo not found")
    return ingestion_status[repo_id]


@router.get("/list", response_model=APIResponse)
async def list_repos():
    repos = [s for s in ingestion_status.values() if s.status == "complete"]
    return APIResponse(success=True, message=f"{len(repos)} repos ready", data=repos)


async def _run_ingestion(request: RepoIngestionRequest):
    repo_id = get_repo_id(request.repo_url)
    try:
        metadata, commits = ingest_repo(
            repo_url=request.repo_url,
            branch=request.branch,
            max_commits=request.max_commits,
        )

        # Store in ChromaDB with temporal metadata
        from app.temporal_rag.snapshot_store import store_commit_snapshots
        store_commit_snapshots(metadata, commits)

        ingestion_status[repo_id] = IngestionStatus(
            repo_id=repo_id,
            status="complete",
            progress=len(commits),
            total=len(commits),
            message=f"Done. {len(commits)} commits embedded. Langs: {metadata.languages}",
        )
        logger.success(f"Ingestion + embedding complete for {repo_id}")
    except Exception as e:
        logger.error(f"Ingestion failed for {repo_id}: {e}")
        ingestion_status[repo_id] = IngestionStatus(
            repo_id=repo_id,
            status="failed",
            progress=0,
            total=0,
            message=str(e),
        )