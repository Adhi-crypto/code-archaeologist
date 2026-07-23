from loguru import logger
from app.reasoning.ollama_client import generate
from app.reasoning.prompt_templates import (
    SYSTEM_REPO_CHAT,
    SYSTEM_CAUSAL,
    repo_chat_prompt,
    causal_reasoning_prompt,
)
from app.temporal_rag.context_builder import build_query_context


async def answer_repo_question(query: str, repo_id: str) -> dict:
    context_str, raw_contexts = build_query_context(query, repo_id, n_results=8)

    prompt = repo_chat_prompt(query, context_str)
    logger.info(f"Answering repo question: '{query[:60]}'")

    answer = await generate(prompt, system=SYSTEM_REPO_CHAT)

    return {
        "answer": answer,
        "sources": [
            {
                "sha": ctx["metadata"].get("commit_sha"),
                "date": ctx["metadata"].get("timestamp", "")[:10],
                "relevance": ctx["relevance_score"],
                "files": ctx["metadata"].get("files_changed", "").split(",")[:3],
            }
            for ctx in raw_contexts[:5]
        ],
        "query": query,
        "repo_id": repo_id,
    }


async def explain_causal(query: str, repo_id: str) -> dict:
    context_str, raw_contexts = build_query_context(query, repo_id, n_results=10)

    prompt = causal_reasoning_prompt(query, context_str)
    logger.info(f"Causal reasoning: '{query[:60]}'")

    answer = await generate(prompt, system=SYSTEM_CAUSAL)

    return {
        "explanation": answer,
        "evidence_commits": [
            {
                "sha": ctx["metadata"].get("commit_sha"),
                "date": ctx["metadata"].get("timestamp", "")[:10],
                "message": next((line.replace("Message: ", "").strip() for line in ctx["document"].split("\n") if line.startswith("Message: ")), "Commit snapshot"),
                "relevance": ctx["relevance_score"],
            }
            for ctx in raw_contexts[:6]
        ],
        "query": query,
        "repo_id": repo_id,
    }