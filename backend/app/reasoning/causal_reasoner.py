from loguru import logger
from app.reasoning.ollama_client import generate
from app.reasoning.prompt_templates import (
    SYSTEM_REPO_CHAT,
    SYSTEM_CAUSAL,
    repo_chat_prompt,
    causal_reasoning_prompt,
)
from app.temporal_rag.context_builder import build_query_context


def classify_query_intent(query: str) -> str:
    """
    Classifies user question into one of 5 technical intent categories:
    - OVERVIEW: High-level repo summary, README, project setup
    - ARCHITECTURE: System design, folder structure, entry points
    - IMPLEMENTATION: Code mechanics, function logic, class details
    - HISTORICAL: Evolution timeline, decision rationale, changes over time
    - BUG_ORIGIN: Error localization, regression tracking
    """
    q = query.lower()

    if any(k in q for k in ["bug", "error", "regression", "crash", "broken", "failed"]):
        return "BUG_ORIGIN"
    elif any(k in q for k in ["why", "reason", "refactored", "history", "evolution", "added", "removed", "change"]):
        return "HISTORICAL"
    elif any(k in q for k in ["how does", "how is", "implementation", "function", "class", "method", "logic", "algorithm", "process", "preprocess"]):
        return "IMPLEMENTATION"
    elif any(k in q for k in ["architecture", "structure", "design", "component", "module", "entry point", "layer"]):
        return "ARCHITECTURE"
    elif any(k in q for k in ["overview", "readme", "about", "what is", "summary", "setup", "install"]):
        return "OVERVIEW"
    else:
        return "IMPLEMENTATION" if len(query.split()) > 4 else "OVERVIEW"


def compute_dynamic_confidence(raw_contexts: list, query: str) -> tuple[int, int]:
    """
    Computes dynamic evidence match score and answer confidence based on:
    - Top vector relevance score
    - Average relevance of top retrieved snapshots
    - Keyword density match
    Returns (evidence_match_score, answer_confidence)
    """
    if not raw_contexts:
        return 15, 20

    relevances = [ctx.get("relevance_score", 0.5) for ctx in raw_contexts]
    top_rel = max(relevances) if relevances else 0.5
    avg_rel = sum(relevances) / max(1, len(relevances))

    # Evidence match score (0 - 100%)
    evidence_match_score = min(98, max(20, int(round((top_rel * 0.7 + avg_rel * 0.3) * 100))))

    # Answer confidence (0 - 100%)
    query_words = [w for w in query.lower().split() if len(w) > 3]
    matches = 0
    total_doc_text = " ".join([ctx.get("document", "").lower() for ctx in raw_contexts[:4]])
    for word in query_words:
        if word in total_doc_text:
            matches += 1

    keyword_density = (matches / max(1, len(query_words))) if query_words else 0.5
    answer_confidence = min(96, max(25, int(round((top_rel * 0.5 + keyword_density * 0.3 + (len(raw_contexts) / 8.0) * 0.2) * 100))))

    return evidence_match_score, answer_confidence


async def answer_repo_question(query: str, repo_id: str) -> dict:
    intent = classify_query_intent(query)
    logger.info(f"Answering repo question [Intent: {intent}]: '{query[:60]}'")

    context_str, raw_contexts = build_query_context(query, repo_id, n_results=8)
    evidence_match, answer_conf = compute_dynamic_confidence(raw_contexts, query)

    # Check for ungrounded query (Low Relevance) to prevent hallucinations
    top_rel = max([ctx.get("relevance_score", 0) for ctx in raw_contexts]) if raw_contexts else 0
    if not raw_contexts or (top_rel < 0.15 and evidence_match < 25):
        return {
            "answer": f"### No Matching Evidence Found\n\nNo relevant implementation, file snapshot, or commit evidence was found in the indexed repository regarding **'{query}'**.\n\n- **Retrieved Evidence Match:** Low ({evidence_match}%)\n- **Suggestion:** Please verify your search terms or try asking about entry points, core routes, or commit evolution.",
            "intent": intent,
            "evidence_match_score": evidence_match,
            "answer_confidence": 20,
            "sources": [],
            "query": query,
            "repo_id": repo_id,
        }

    # Facts vs. Inference System Prompting Strategy
    custom_system = (
        SYSTEM_REPO_CHAT + "\n"
        "IMPORTANT RULES FOR ACCURACY:\n"
        "1. Facts vs Inference: Clearly distinguish between Observed Evidence (direct facts from code/diffs) and AI Inference (derived conclusions).\n"
        "2. Do NOT hallucinate methods, classes, or files not present in the evidence.\n"
        "3. Address the intent directly: Explain code logic for IMPLEMENTATION, system structure for ARCHITECTURE, or commit history for HISTORICAL questions."
    )

    prompt = repo_chat_prompt(query, context_str)
    answer = await generate(prompt, system=custom_system)

    return {
        "answer": answer,
        "intent": intent,
        "evidence_match_score": evidence_match,
        "answer_confidence": answer_conf,
        "sources": [
            {
                "sha": ctx["metadata"].get("commit_sha"),
                "date": ctx["metadata"].get("timestamp", "")[:10],
                "relevance": ctx["relevance_score"],
                "files": [f.strip() for f in ctx["metadata"].get("files_changed", "").split(",") if f.strip()][:4],
            }
            for ctx in raw_contexts[:5]
        ],
        "query": query,
        "repo_id": repo_id,
    }


async def explain_causal(query: str, repo_id: str) -> dict:
    intent = classify_query_intent(query)
    logger.info(f"Causal reasoning [Intent: {intent}]: '{query[:60]}'")

    context_str, raw_contexts = build_query_context(query, repo_id, n_results=10)
    evidence_match, answer_conf = compute_dynamic_confidence(raw_contexts, query)

    # Check for ungrounded query
    top_rel = max([ctx.get("relevance_score", 0) for ctx in raw_contexts]) if raw_contexts else 0
    if not raw_contexts or (top_rel < 0.15 and evidence_match < 25):
        return {
            "explanation": f"### No Historical Context Found\n\nNo relevant commit history or diff evidence was found in the indexed repository regarding **'{query}'**.\n\n- **Evidence Match:** Low ({evidence_match}%)\n- **Suggestion:** Please check query spelling or ingest a repository with a longer commit history.",
            "intent": intent,
            "evidence_match_score": evidence_match,
            "answer_confidence": 20,
            "evidence_commits": [],
            "query": query,
            "repo_id": repo_id,
        }

    custom_system = (
        SYSTEM_CAUSAL + "\n"
        "IMPORTANT RULES:\n"
        "1. Facts vs Inference: Clearly state observed evidence vs inferred reasoning.\n"
        "2. Do NOT speculate without citing commit evidence."
    )

    prompt = causal_reasoning_prompt(query, context_str)
    answer = await generate(prompt, system=custom_system)

    return {
        "explanation": answer,
        "intent": intent,
        "evidence_match_score": evidence_match,
        "answer_confidence": answer_conf,
        "evidence_commits": [
            {
                "sha": ctx["metadata"].get("commit_sha"),
                "date": ctx["metadata"].get("timestamp", "")[:10],
                "message": next((line.replace("Message: ", "").strip() for line in ctx["document"].split("\n") if line.startswith("Message: ")), "Commit snapshot"),
                "relevance": ctx["relevance_score"],
                "files": [f.strip() for f in ctx["metadata"].get("files_changed", "").split(",") if f.strip()][:4],
            }
            for ctx in raw_contexts[:6]
        ],
        "query": query,
        "repo_id": repo_id,
    }