import time
import hashlib
from functools import lru_cache
from loguru import logger
from datetime import datetime
from app.temporal_rag.snapshot_store import get_collection
from app.temporal_rag.embedder import embed_text

from typing import Optional

_vector_search_cache: dict[tuple, list[dict]] = {}
_overview_cache: dict[str, dict] = {}


def invalidate_retrieval_cache(repo_id: str = None):
    global _vector_search_cache, _overview_cache
    if repo_id:
        _overview_cache.pop(repo_id, None)
        keys_to_del = [k for k in _vector_search_cache if k[0] == repo_id]
        for k in keys_to_del:
            del _vector_search_cache[k]
        logger.info(f"[CACHE INVALIDATED] Retrieval cache cleared for repo {repo_id}")
    else:
        _vector_search_cache.clear()
        _overview_cache.clear()
        logger.info("[CACHE INVALIDATED] All retrieval caches cleared")


def _retrieval_cache_key(query: str, repo_id: str, n_results: int, time_from: Optional[datetime], time_to: Optional[datetime]) -> tuple:
    q_hash = hashlib.sha256(query.lower().strip().encode("utf-8")).hexdigest()
    tf_unix = int(time_from.timestamp()) if time_from else None
    tt_unix = int(time_to.timestamp()) if time_to else None
    return (repo_id, q_hash, n_results, tf_unix, tt_unix)


def _detect_positional_commit_index(query: str) -> Optional[int]:
    """Detects positional commit requests in natural language queries."""
    q = query.lower()
    if any(k in q for k in ["first commit", "1st commit", "initial commit", "beginning commit"]):
        return 0
    elif any(k in q for k in ["second commit", "2nd commit"]):
        return 1
    elif any(k in q for k in ["third commit", "3rd commit"]):
        return 2
    elif any(k in q for k in ["fourth commit", "4th commit"]):
        return 3
    elif any(k in q for k in ["fifth commit", "5th commit"]):
        return 4
    elif any(k in q for k in ["latest commit", "last commit", "most recent commit", "recent commit"]):
        return -1  # indicates latest
    return None


def retrieve_temporal_context(
    query: str,
    repo_id: str,
    n_results: int = 8,
    time_from: Optional[datetime] = None,
    time_to: Optional[datetime] = None,
) -> list[dict]:
    """
    Retrieve relevant commit snapshots using a 2-stage RAG pipeline:
    - Stage 0: Positional & Overview Intent Handling (fetch exact commit index or repo_summary)
    - Stage 1: Broad semantic search (retrieve candidate pool of Top 20)
    - Stage 2: Multi-factor re-ranking (vector score + keyword density + recency) to pick Top N
    """
    cache_k = _retrieval_cache_key(query, repo_id, n_results, time_from, time_to)
    if cache_k in _vector_search_cache:
        logger.info(f"RAG Cache HIT [<1ms]: '{query[:40]}'")
        return _vector_search_cache[cache_k]

    t_start = time.perf_counter()
    collection = get_collection()

    final_contexts = []
    
    # 1. Deterministic Positional Commit Resolution
    target_idx = _detect_positional_commit_index(query)
    if target_idx is not None:
        try:
            pos_res = collection.get(
                where={"repo_id": repo_id},
                include=["documents", "metadatas"],
            )
            if pos_res and pos_res.get("metadatas"):
                matched_metas = []
                for doc, meta in zip(pos_res["documents"], pos_res["metadatas"]):
                    if meta.get("doc_type") == "commit_snapshot":
                        matched_metas.append((doc, meta))
                
                matched_metas.sort(key=lambda x: x[1].get("commit_index", 0))
                
                actual_idx = target_idx if target_idx >= 0 else len(matched_metas) - 1
                if 0 <= actual_idx < len(matched_metas):
                    doc, meta = matched_metas[actual_idx]
                    logger.info(f"Positional Retrieval HIT for index {actual_idx}: SHA={meta.get('commit_sha')}")
                    final_contexts.append({
                        "document": doc,
                        "metadata": meta,
                        "relevance_score": 0.98,
                        "rerank_score": 0.99,
                    })
        except Exception as e:
            logger.warning(f"Positional commit query failed: {e}")

    # 2. Deterministic Overview Summary Resolution (with in-memory cache)
    is_overview_query = any(k in query.lower() for k in ["about", "overview", "explain the project", "what is this", "architecture", "structure", "summary"])
    if is_overview_query or not final_contexts:
        if repo_id in _overview_cache:
            final_contexts.insert(0, _overview_cache[repo_id])
        else:
            try:
                overview_res = collection.get(
                    ids=[f"{repo_id}_overview"],
                    include=["documents", "metadatas"],
                )
                if overview_res and overview_res.get("documents") and overview_res["documents"][0]:
                    doc = overview_res["documents"][0]
                    meta = overview_res["metadatas"][0]
                    cached_overview = {
                        "document": doc,
                        "metadata": meta,
                        "relevance_score": 0.95,
                        "rerank_score": 0.98,
                    }
                    _overview_cache[repo_id] = cached_overview
                    final_contexts.insert(0, cached_overview)
            except Exception as e:
                logger.debug(f"Overview summary fetch notice: {e}")

    t0 = time.perf_counter()
    query_embedding = embed_text(query)
    t_embed_ms = round((time.perf_counter() - t0) * 1000, 2)

    where_filter = {"repo_id": repo_id}

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

    fetch_limit = min(20, max(5, n_results * 2))

    t1 = time.perf_counter()
    results = None
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        logger.warning(f"ChromaDB direct KNN query notice ({e}), falling back to collection.get()")
        try:
            get_res = collection.get(
                where=where_filter,
                limit=fetch_limit,
                include=["documents", "metadatas"],
            )
            if get_res and get_res.get("documents"):
                results = {
                    "documents": [get_res["documents"]],
                    "metadatas": [get_res["metadatas"]],
                    "distances": [[0.3] * len(get_res["documents"])],
                }
        except Exception as e2:
            logger.error(f"Fallback get query also failed: {e2}")
    t_vsearch_ms = round((time.perf_counter() - t1) * 1000, 2)


    t2 = time.perf_counter()
    candidates = []
    existing_shas = {c["metadata"].get("commit_sha") for c in final_contexts}

    if results and results["documents"] and results["documents"][0]:
        query_words = set(w.lower() for w in query.split() if len(w) > 2)
        total_candidates = len(results["documents"][0])

        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            if meta.get("commit_sha") in existing_shas:
                continue

            # Calibrate Cosine Distance mapping for dense 384-d vectors
            sem_score = round(max(0.15, min(0.99, 1.0 - (dist * 0.5))), 3)

            doc_lower = doc.lower()
            kw_matches = sum(1 for w in query_words if w in doc_lower)
            kw_score = (kw_matches / max(1, len(query_words))) if query_words else 0.5

            recency_score = (total_candidates - i) / float(total_candidates)

            rerank_score = round((sem_score * 0.6) + (kw_score * 0.25) + (recency_score * 0.15), 3)

            candidates.append({
                "document": doc,
                "metadata": meta,
                "relevance_score": sem_score,
                "rerank_score": rerank_score,
            })

    candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
    
    # Merge candidates into final_contexts
    remaining_slots = max(1, n_results - len(final_contexts))
    final_contexts.extend(candidates[:remaining_slots])

    t_rerank_ms = round((time.perf_counter() - t2) * 1000, 2)
    t_total_ms = round((time.perf_counter() - t_start) * 1000, 2)

    logger.info(
        f"RAG Retrieval Timing for '{query[:40]}': Total={t_total_ms}ms "
        f"[Embedding={t_embed_ms}ms, VectorSearch={t_vsearch_ms}ms, Rerank={t_rerank_ms}ms, Contexts={len(final_contexts)}]"
    )

    _vector_search_cache[cache_k] = final_contexts
    return final_contexts



def build_temporal_context_string(contexts: list[dict]) -> str:
    """Format retrieved contexts into a prompt-ready string with automatic token compression."""
    if not contexts:
        return "No relevant commit history found."

    parts = []
    seen_shas = set()

    for i, ctx in enumerate(contexts, 1):
        meta = ctx["metadata"]
        sha = meta.get('commit_sha', '')
        if sha in seen_shas:
            continue
        seen_shas.add(sha)

        doc = ctx['document']
        # Compress prompt string: strip repetitive Repository name lines & format compactly
        compact_lines = []
        for line in doc.split("\n"):
            if line.startswith("Repository: "):
                continue  # strip redundant repo name line per snapshot
            compact_lines.append(line)
        
        compact_doc = "\n".join(compact_lines).strip()

        parts.append(
            f"[Snapshot {i} | {meta.get('timestamp', '')[:10]} | "
            f"Score: {ctx['relevance_score']} | SHA: {sha}]\n"
            f"{compact_doc}"
        )
    return "\n\n---\n\n".join(parts)
