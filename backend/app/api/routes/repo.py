import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
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


class RepoIntelligenceRequest(BaseModel):
    repo_id: str
    repo_name: str = "Repository"
    deterministic_only: bool = False


@router.post("/intelligence", response_model=APIResponse)
async def get_repository_intelligence(request: RepoIntelligenceRequest):
    from app.reasoning.repository_intelligence import analyze_repository_intelligence, get_deterministic_intelligence
    try:
        if request.deterministic_only:
            result = get_deterministic_intelligence(request.repo_id, request.repo_name)
        else:
            result = await analyze_repository_intelligence(request.repo_id, request.repo_name)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return APIResponse(success=True, message="Repository intelligence generated", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Repository intelligence failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



async def _run_ingestion(request: RepoIngestionRequest):
    repo_id = get_repo_id(request.repo_url)
    try:
        ingestion_status[repo_id] = IngestionStatus(
            repo_id=repo_id,
            status="running",
            progress=0,
            total=request.max_commits,
            message="Extracting commits and diff history from Git...",
        )

        # Offload sync Git cloning & commit extraction
        metadata, commits, overview_info = await asyncio.to_thread(
            ingest_repo,
            repo_url=request.repo_url,
            branch=request.branch,
            max_commits=request.max_commits,
        )

        ingestion_status[repo_id] = IngestionStatus(
            repo_id=repo_id,
            status="running",
            progress=int(len(commits) * 0.2),
            total=len(commits),
            message=f"Extracted {len(commits)} commits. Analyzing languages and structure...",
        )

        def progress_cb(stage_msg: str, current: int, total_items: int):
            pct = 0.2 + (0.75 * (current / max(1, total_items)))
            ingestion_status[repo_id] = IngestionStatus(
                repo_id=repo_id,
                status="running",
                progress=int(len(commits) * pct),
                total=len(commits),
                message=stage_msg,
            )

        # Store in ChromaDB with temporal metadata & overview info (offloaded sync vector embeddings)
        from app.temporal_rag.snapshot_store import store_commit_snapshots
        await asyncio.to_thread(store_commit_snapshots, metadata, commits, overview_info, progress_cb)

        # Invalidate caches for freshly ingested repo
        from app.reasoning.repository_intelligence import invalidate_intelligence_cache
        from app.reasoning.evolution_detector import invalidate_evolution_cache
        from app.temporal_rag.temporal_retriever import invalidate_retrieval_cache
        from app.reasoning.ollama_client import invalidate_llm_cache

        invalidate_intelligence_cache(repo_id)
        invalidate_evolution_cache(repo_id)
        invalidate_retrieval_cache(repo_id)
        invalidate_llm_cache()

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