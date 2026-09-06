import time
import hashlib
from functools import lru_cache
from loguru import logger
from datetime import datetime
from app.temporal_rag.snapshot_store import get_collection
from app.temporal_rag.embedder import embed_text

from typing import Optional

_vector_search_cache: dict[tuple, list[dict]] = {}


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
    doc_count = collection.count()
    if doc_count == 0:
        return []

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

    # 2. Deterministic Overview Summary Resolution
    is_overview_query = any(k in query.lower() for k in ["about", "overview", "explain the project", "what is this", "architecture", "structure", "summary"])
    if is_overview_query or not final_contexts:
        try:
            overview_res = collection.get(
                ids=[f"{repo_id}_overview"],
                include=["documents", "metadatas"],
            )
            if overview_res and overview_res.get("documents") and overview_res["documents"][0]:
                doc = overview_res["documents"][0]
                meta = overview_res["metadatas"][0]
                final_contexts.insert(0, {
                    "document": doc,
                    "metadata": meta,
                    "relevance_score": 0.95,
                    "rerank_score": 0.98,
                })
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

    # Determine actual matching document count for the target repo to prevent HNSW contiguous array errors
    matching_ids = []
    try:
        matched_get = collection.get(where=where_filter, include=[])
        if matched_get and matched_get.get("ids"):
            matching_ids = matched_get["ids"]
    except Exception as e:
        logger.warning(f"Could not fetch matching IDs count for repo {repo_id}: {e}")

    actual_match_count = len(matching_ids)
    if actual_match_count == 0:
        # Retry with basic repo_id filter
        where_filter = {"repo_id": repo_id}
        try:
            matched_get = collection.get(where=where_filter, include=[])
            if matched_get and matched_get.get("ids"):
                actual_match_count = len(matched_get["ids"])
        except Exception:
            pass

    fetch_limit = min(20, max(1, actual_match_count)) if actual_match_count > 0 else min(20, doc_count)

    t1 = time.perf_counter()
    results = None
    if actual_match_count > 0:
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=fetch_limit,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.warning(f"ChromaDB KNN query failed ({e}), falling back to collection.get()")
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
