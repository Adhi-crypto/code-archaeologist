from app.temporal_rag.temporal_retriever import retrieve_temporal_context, build_temporal_context_string
from datetime import datetime


from typing import Optional, Tuple

def build_query_context(
    query: str,
    repo_id: str,
    time_from: Optional[datetime] = None,
    time_to: Optional[datetime] = None,
    n_results: int = 8,
) -> Tuple[str, list]:
    """Returns (formatted_context_string, raw_contexts)"""
    contexts = retrieve_temporal_context(
        query=query,
        repo_id=repo_id,
        n_results=n_results,
        time_from=time_from,
        time_to=time_to,
    )
    context_str = build_temporal_context_string(contexts)
    return context_str, contexts 