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


@router.post("", response_model=dict)
@router.post("/", response_model=dict)
@router.post("/analyze", response_model=dict)
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


class DebugRetrievalRequest(BaseModel):

    repo_id: str
    query: str

@router.post("/debug-retrieval", response_model=dict)
async def debug_retrieval(request: DebugRetrievalRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        from app.temporal_rag.snapshot_store import get_collection
        from app.temporal_rag.temporal_retriever import retrieve_temporal_context, build_temporal_context_string
        from app.reasoning.causal_reasoner import classify_query_intent, compute_dynamic_confidence

        collection = get_collection()
        total_vectors = collection.count()
        intent = classify_query_intent(request.query)

        contexts = retrieve_temporal_context(request.query, request.repo_id, n_results=10)
        evidence_match, answer_conf = compute_dynamic_confidence(contexts, request.query)
        prompt_ctx = build_temporal_context_string(contexts)

        candidates = []
        for rank, ctx in enumerate(contexts, 1):
            meta = ctx.get("metadata", {})
            doc = ctx.get("document", "")
            candidates.append({
                "rank": rank,
                "doc_type": meta.get("doc_type", "commit_snapshot"),
                "sha": meta.get("commit_sha", ""),
                "commit_index": meta.get("commit_index", -1),
                "relevance_score": ctx.get("relevance_score", 0),
                "rerank_score": ctx.get("rerank_score", 0),
                "author": meta.get("author", ""),
                "snippet": doc[:250] + "...",
            })

        return {
            "success": True,
            "data": {
                "query": request.query,
                "repo_id": request.repo_id,
                "intent": intent,
                "total_collection_vectors": total_vectors,
                "evidence_match_score": evidence_match,
                "answer_confidence": answer_conf,
                "retrieved_count": len(contexts),
                "prompt_context_length": len(prompt_ctx),
                "estimated_prompt_tokens": len(prompt_ctx.split()),
                "candidates": candidates,
                "prompt_context_snippet": prompt_ctx[:1000] + "...",
            }
        }
    except Exception as e:
        logger.error(f"Debug retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

