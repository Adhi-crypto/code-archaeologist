from loguru import logger
from app.reasoning.ollama_client import generate
from app.reasoning.prompt_templates import SYSTEM_EVOLUTION, evolution_prompt
from app.temporal_rag.snapshot_store import get_collection


async def detect_evolution(repo_id: str, repo_name: str) -> dict:
    collection = get_collection()

    results = collection.get(
        where={"repo_id": repo_id},
        include=["documents", "metadatas"],
    )

    if not results or not results["documents"]:
        return {"error": "No data found for this repo"}

    # Sort chronologically, take evenly spaced samples for the prompt
    combined = list(zip(results["documents"], results["metadatas"]))
    combined.sort(key=lambda x: x[1].get("timestamp_unix", 0))

    # Sample up to 20 commits evenly across the timeline
    step = max(1, len(combined) // 20)
    sampled = combined[::step][:20]

    context = "\n\n---\n\n".join([doc for doc, _ in sampled])
    prompt = evolution_prompt(repo_name, context)

    logger.info(f"Detecting evolution for {repo_name} ({len(sampled)} sampled commits)")
    narrative = await generate(prompt, system=SYSTEM_EVOLUTION)

    timeline = [
        {
            "date": meta.get("timestamp", "")[:10],
            "sha": meta.get("commit_sha"),
            "message": doc.split("\n")[4].replace("Message: ", "")[:80],
            "files": meta.get("files_changed", "").split(",")[:3],
        }
        for doc, meta in sampled
    ]

    return {
        "repo_id": repo_id,
        "repo_name": repo_name,
        "narrative": narrative,
        "timeline": timeline,
        "commits_analyzed": len(combined),
        "commits_sampled": len(sampled),
    }