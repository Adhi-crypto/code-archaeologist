import json
import time
from loguru import logger
from app.reasoning.ollama_client import generate, generate_stream
from app.reasoning.prompt_templates import (
    SYSTEM_REPO_CHAT,
    SYSTEM_CAUSAL,
    repo_chat_prompt,
    causal_reasoning_prompt,
)
from app.temporal_rag.context_builder import build_query_context


def classify_query_intent(query: str) -> str:
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


def get_adaptive_n_results(intent: str) -> int:
    """Adaptive Top-K retrieval count: Simple queries use fewer prefill tokens, complex queries use deeper history."""
    return {
        "OVERVIEW": 3,
        "ARCHITECTURE": 4,
        "IMPLEMENTATION": 5,
        "HISTORICAL": 7,
        "BUG_ORIGIN": 8,
    }.get(intent, 5)


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
    intent = classify_query_intent(query)
    n_results = get_adaptive_n_results(intent)
    logger.info(f"Answering repo question [Intent: {intent}, Top-K: {n_results}]: '{query[:60]}'")

    context_str, raw_contexts = build_query_context(query, repo_id, n_results=n_results)
    evidence_match, answer_conf = compute_dynamic_confidence(raw_contexts, query)

    top_rel = max([ctx.get("relevance_score", 0) for ctx in raw_contexts]) if raw_contexts else 0
    if not raw_contexts or (top_rel < 0.05 and evidence_match < 15):
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


async def answer_repo_question_stream(query: str, repo_id: str, mode: str = "chat"):
    """Yields SSE events: status, metadata header, then real-time LLM token stream."""
    t_start = time.perf_counter()
    yield f"event: status\ndata: {json.dumps({'message': 'Analyzing query intent & checking RAG vector cache...'})}\n\n"

    intent = classify_query_intent(query)
    n_results = get_adaptive_n_results(intent)

    yield f"event: status\ndata: {json.dumps({'message': f'Searching commit history snapshots [Top-K: {n_results}]...'})}\n\n"

    t0 = time.perf_counter()
    context_str, raw_contexts = build_query_context(query, repo_id, n_results=n_results)
    rag_ms = round((time.perf_counter() - t0) * 1000, 2)

    evidence_match, answer_conf = compute_dynamic_confidence(raw_contexts, query)
    sources = [
        {
            "sha": ctx["metadata"].get("commit_sha"),
            "date": ctx["metadata"].get("timestamp", "")[:10],
            "relevance": ctx["relevance_score"],
            "files": [f.strip() for f in ctx["metadata"].get("files_changed", "").split(",") if f.strip()][:4],
        }
        for ctx in raw_contexts[:6]
    ]

    # Emit metadata SSE event
    meta_payload = {
        "intent": intent,
        "evidence_match_score": evidence_match,
        "answer_confidence": answer_conf,
        "sources": sources,
        "query": query,
        "repo_id": repo_id,
        "mode": mode,
        "rag_latency_ms": rag_ms,
    }
    yield f"event: metadata\ndata: {json.dumps(meta_payload)}\n\n"

    top_rel = max([ctx.get("relevance_score", 0) for ctx in raw_contexts]) if raw_contexts else 0
    if not raw_contexts or (top_rel < 0.05 and evidence_match < 15):
        fallback = f"### No Matching Evidence Found\n\nNo relevant commit history or diff evidence was found in the indexed repository regarding **'{query}'**.\n\n- **Retrieved Evidence Match:** Low ({evidence_match}%)\n- **Suggestion:** Please check search query spelling or try asking about core entry points or commit evolution."

        yield f"event: token\ndata: {json.dumps({'token': fallback})}\n\n"
        yield f"event: done\ndata: {json.dumps({'ttft_ms': round((time.perf_counter() - t_start) * 1000, 2)})}\n\n"
        return

    if mode == "causal":
        custom_system = (
            SYSTEM_CAUSAL + "\n"
            "IMPORTANT RULES:\n"
            "1. Facts vs Inference: Clearly state observed evidence vs inferred reasoning.\n"
            "2. Do NOT speculate without citing commit evidence."
        )
        prompt = causal_reasoning_prompt(query, context_str)
    else:
        custom_system = (
            SYSTEM_REPO_CHAT + "\n"
            "IMPORTANT RULES FOR ACCURACY:\n"
            "1. Facts vs Inference: Clearly distinguish between Observed Evidence (direct facts from code/diffs) and AI Inference (derived conclusions).\n"
            "2. Do NOT hallucinate methods, classes, or files not present in the evidence.\n"
            "3. Address the intent directly: Explain code logic for IMPLEMENTATION, system structure for ARCHITECTURE, or commit history for HISTORICAL questions."
        )
        prompt = repo_chat_prompt(query, context_str)

    yield f"event: status\ndata: {json.dumps({'message': 'Synthesizing response with Ollama LLM engine...'})}\n\n"

    t_first_token = None
    token_count = 0
    try:
        async for token in generate_stream(prompt, system=custom_system):
            if t_first_token is None:
                t_first_token = time.perf_counter()
            token_count += 1
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
    except Exception as e:
        logger.error(f"Stream generation error in causal_reasoner: {e}")
        fallback_msg = f"\n\n*(Note: Local Ollama LLM stream error: {e}. Outputting retrieved evidence context.)*\n\n{context_str[:500]}..."
        yield f"event: token\ndata: {json.dumps({'token': fallback_msg})}\n\n"

    ttft_ms = round((t_first_token - t_start) * 1000, 2) if t_first_token else round((time.perf_counter() - t_start) * 1000, 2)
    ttlt_ms = round((time.perf_counter() - t_start) * 1000, 2)
    logger.info(f"Stream Complete for '{query[:40]}': TTFT={ttft_ms}ms, TTLT={ttlt_ms}ms, Tokens={token_count}")

    yield f"event: done\ndata: {json.dumps({'ttft_ms': ttft_ms, 'ttlt_ms': ttlt_ms, 'tokens': token_count})}\n\n"



async def explain_causal(query: str, repo_id: str) -> dict:
    intent = classify_query_intent(query)
    n_results = get_adaptive_n_results(intent)
    logger.info(f"Causal reasoning [Intent: {intent}, Top-K: {n_results}]: '{query[:60]}'")

    context_str, raw_contexts = build_query_context(query, repo_id, n_results=n_results)
    evidence_match, answer_conf = compute_dynamic_confidence(raw_contexts, query)

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