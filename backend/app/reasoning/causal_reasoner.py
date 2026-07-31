import time
from loguru import logger
from app.core.config import settings
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
    if not raw_contexts:
        return 15, 20

    relevances = [ctx.get("relevance_score", 0.5) for ctx in raw_contexts]
    top_rel = max(relevances) if relevances else 0.5
    avg_rel = sum(relevances) / max(1, len(relevances))

    evidence_match_score = min(98, max(20, int(round((top_rel * 0.7 + avg_rel * 0.3) * 100))))

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
    start_time = time.time()
    logger.info(f"[STAGE 1 START Query] Query: '{query}' | Repo ID: {repo_id}")

    intent = classify_query_intent(query)
    logger.info(f"[STAGE 2 Intent Classified] Category: {intent}")

    context_str, raw_contexts = build_query_context(query, repo_id, n_results=8)
    logger.info(f"[STAGE 3 Temporal Retrieval] Retrieved {len(raw_contexts)} commit snapshots from ChromaDB")

    evidence_match, answer_conf = compute_dynamic_confidence(raw_contexts, query)

    # Check for low relevance ungrounded query
    top_rel = max([ctx.get("relevance_score", 0) for ctx in raw_contexts]) if raw_contexts else 0
    if not raw_contexts or (top_rel < 0.15 and evidence_match < 25):
        exec_time = round(time.time() - start_time, 3)
        logger.info(f"[STAGE COMPLETE] Low relevance score ({top_rel:.2f}). Returning non-hallucination notice in {exec_time}s")
        return {
            "answer": f"### No Matching Evidence Found\n\nNo relevant implementation, file snapshot, or commit evidence was found in the indexed repository regarding **'{query}'**.\n\n- **Retrieved Evidence Match:** Low ({evidence_match}%)\n- **Suggestion:** Please verify your search terms or try asking about entry points, core routes, or commit evolution.",
            "intent": intent,
            "evidence_match_score": evidence_match,
            "answer_confidence": 20,
            "sources": [],
            "query": query,
            "repo_id": repo_id,
        }

    custom_system = (
        SYSTEM_REPO_CHAT + "\n"
        "IMPORTANT RULES FOR ACCURACY:\n"
        "1. Facts vs Inference: Clearly distinguish between Observed Evidence (direct facts from code/diffs) and AI Inference (derived conclusions).\n"
        "2. Do NOT hallucinate methods, classes, or files not present in the evidence.\n"
        "3. Address the intent directly: Explain code logic for IMPLEMENTATION, system structure for ARCHITECTURE, or commit history for HISTORICAL questions."
    )

    prompt = repo_chat_prompt(query, context_str)
    logger.info(f"[STAGE 4 Prompt Construction] Prompt Length: {len(prompt)} chars | System Length: {len(custom_system)} chars")

    logger.info(f"[STAGE 5 LLM API Call] Provider: Ollama | Model: {settings.OLLAMA_MODEL}")
    try:
        answer = await generate(prompt, system=custom_system)
        logger.info(f"[STAGE 6 LLM Response Success] Received {len(answer)} chars from Ollama")
    except Exception as e:
        logger.warning(f"[STAGE 6 LLM Fallback] Ollama call failed: {e}. Generating grounded algorithmic summary.", exc_info=True)
        top_commits = []
        for ctx in raw_contexts[:4]:
            sha = ctx["metadata"].get("commit_sha", "unknown")
            author = ctx["metadata"].get("author", "unknown")
            date = ctx["metadata"].get("timestamp", "")[:10]
            files = ctx["metadata"].get("files_changed", "")
            top_commits.append(f"- Commit `{sha}` by **{author}** ({date}) modifying `{files}`")

        commits_summary = "\n".join(top_commits) if top_commits else "No specific commits found."
        answer = (
            f"### Grounded Evidence Analysis for **'{query}'**\n\n"
            f"*(Note: Local Ollama LLM is offline or model `{settings.OLLAMA_MODEL}` is not loaded. Displaying grounded evidence retrieved from ChromaDB vector store.)*\n\n"
            f"#### Matching Repository Commit Evidence:\n"
            f"{commits_summary}\n\n"
            f"**Evidence Summary:** Discovered {len(raw_contexts)} commit snapshots in ChromaDB matching query `{query}`. "
            f"Top snapshot has {evidence_match}% relevance match."
        )

    exec_time = round(time.time() - start_time, 3)
    logger.info(f"[STAGE COMPLETE Execution Time: {exec_time}s] Successfully processed query '{query[:30]}'")

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
    start_time = time.time()
    logger.info(f"[STAGE 1 START Causal Query] Query: '{query}' | Repo ID: {repo_id}")

    intent = classify_query_intent(query)
    logger.info(f"[STAGE 2 Intent Classified] Category: {intent}")

    context_str, raw_contexts = build_query_context(query, repo_id, n_results=10)
    logger.info(f"[STAGE 3 Temporal Retrieval] Retrieved {len(raw_contexts)} commit snapshots from ChromaDB")

    evidence_match, answer_conf = compute_dynamic_confidence(raw_contexts, query)

    top_rel = max([ctx.get("relevance_score", 0) for ctx in raw_contexts]) if raw_contexts else 0
    if not raw_contexts or (top_rel < 0.15 and evidence_match < 25):
        exec_time = round(time.time() - start_time, 3)
        logger.info(f"[STAGE COMPLETE] Low relevance score ({top_rel:.2f}). Returning non-hallucination notice in {exec_time}s")
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
    logger.info(f"[STAGE 4 Prompt Construction] Prompt Length: {len(prompt)} chars | System Length: {len(custom_system)} chars")

    logger.info(f"[STAGE 5 LLM API Call] Provider: Ollama | Model: {settings.OLLAMA_MODEL}")
    try:
        answer = await generate(prompt, system=custom_system)
        logger.info(f"[STAGE 6 LLM Response Success] Received {len(answer)} chars from Ollama")
    except Exception as e:
        logger.warning(f"[STAGE 6 LLM Fallback] Ollama call failed: {e}. Generating grounded causal summary.", exc_info=True)
        top_commits = []
        for ctx in raw_contexts[:4]:
            sha = ctx["metadata"].get("commit_sha", "unknown")
            author = ctx["metadata"].get("author", "unknown")
            date = ctx["metadata"].get("timestamp", "")[:10]
            files = ctx["metadata"].get("files_changed", "")
            top_commits.append(f"- Commit `{sha}` by **{author}** ({date}) modifying `{files}`")

        commits_summary = "\n".join(top_commits) if top_commits else "No specific commits found."
        answer = (
            f"### Historical Evidence Rationale for **'{query}'**\n\n"
            f"*(Note: Local Ollama LLM is offline or model `{settings.OLLAMA_MODEL}` is not loaded. Displaying causal evidence retrieved from ChromaDB vector store.)*\n\n"
            f"#### Retrieved Commit Evidence:\n"
            f"{commits_summary}\n\n"
            f"**Causal Evidence:** Analyzed {len(raw_contexts)} commit snapshots in ChromaDB matching query `{query}`. "
            f"Evidence indicates key changes concentrated around these commits."
        )

    exec_time = round(time.time() - start_time, 3)
    logger.info(f"[STAGE COMPLETE Execution Time: {exec_time}s] Successfully processed causal query '{query[:30]}'")

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