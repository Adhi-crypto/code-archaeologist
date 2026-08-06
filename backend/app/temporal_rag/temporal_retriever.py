from loguru import logger
from datetime import datetime
from app.temporal_rag.snapshot_store import get_collection
from app.temporal_rag.embedder import embed_text


from typing import Optional

def retrieve_temporal_context(
    query: str,
    repo_id: str,
    n_results: int = 8,
    time_from: Optional[datetime] = None,
    time_to: Optional[datetime] = None,
) -> list[dict]:
    """
    Retrieve relevant commit snapshots using time-aware semantic search.
    Optionally filter by time range to answer evolution questions.
    """
    collection = get_collection()
    query_embedding = embed_text(query)

    where_filter = {"repo_id": repo_id}

    # Add time range filter if provided
    if time_from and time_to:
        where_filter = {
            "$and": [
                {"repo_id": {"$eq": repo_id}},
                {"timestamp_unix": {"$gte": int(time_from.timestamp())}},
                {"timestamp_unix": {"$lte": int(time_to.timestamp())}},
            ]
        }
    elif time_from:
        where_filter = {
            "$and": [
                {"repo_id": {"$eq": repo_id}},
                {"timestamp_unix": {"$gte": int(time_from.timestamp())}},
            ]
        }

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        logger.warning(f"Temporal query failed, falling back to basic: {e}")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, collection.count()),
            where={"repo_id": repo_id},
            include=["documents", "metadatas", "distances"],
        )

    contexts = []
    if results and results["documents"]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            contexts.append({
                "document": doc,
                "metadata": meta,
                "relevance_score": round(1 - dist, 3),
            })

    # Sort by timestamp so LLM sees chronological order
    contexts.sort(key=lambda x: x["metadata"].get("timestamp_unix", 0))
    logger.info(f"Retrieved {len(contexts)} temporal contexts for query: '{query[:60]}'")
    return contexts


def build_temporal_context_string(contexts: list[dict]) -> str:
    """Format retrieved contexts into a prompt-ready string."""
    if not contexts:
        return "No relevant commit history found."

    parts = []
    for i, ctx in enumerate(contexts, 1):
        meta = ctx["metadata"]
        parts.append(
            f"[Snapshot {i} | {meta.get('timestamp', '')[:10]} | "
            f"Score: {ctx['relevance_score']} | SHA: {meta.get('commit_sha', '')}]\n"
            f"{ctx['document']}"
        )
    return "\n\n---\n\n".join(parts)