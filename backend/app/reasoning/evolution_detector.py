from loguru import logger
from app.reasoning.ollama_client import generate
from app.reasoning.prompt_templates import SYSTEM_EVOLUTION, evolution_prompt
from app.temporal_rag.snapshot_store import get_collection


def compute_importance(additions: int, deletions: int, files_changed: list[str]) -> float:
    """Compute commit importance score (0-100) based on diff magnitude and file scope."""
    total_churn = additions + deletions
    num_files = len(files_changed)
    
    churn_score = min(50.0, (total_churn / 200.0) * 50.0)
    file_score = min(30.0, (num_files / 10.0) * 30.0)
    
    crit_keywords = ["main", "config", "core", "routes", "api", "schema", "model", "docker", "auth", "rag", "engine"]
    crit_bonus = 20.0 if any(any(k in f.lower() for k in crit_keywords) for f in files_changed) else 0.0
    
    return min(100.0, round(churn_score + file_score + crit_bonus, 1))


def is_arch_change(files_changed: list[str], additions: int, deletions: int) -> bool:
    """Determine if a commit represents an architectural change."""
    arch_files = ["main", "config", "docker", "schema", "routes", "architecture", "models", "core", "pipeline"]
    has_arch_file = any(any(af in f.lower() for af in arch_files) for f in files_changed)
    high_churn = (additions + deletions) > 150 or len(files_changed) >= 5
    return has_arch_file or high_churn


def classify_impact(is_arch: bool, total_churn: int) -> str:
    if is_arch and total_churn > 200:
        return "Major Architecture Shift"
    elif is_arch:
        return "Architectural Update"
    elif total_churn > 300:
        return "Major Refactor"
    elif total_churn > 50:
        return "Feature Enhancement"
    else:
        return "Routine Maintenance"


async def detect_evolution(repo_id: str, repo_name: str) -> dict:
    collection = get_collection()

    results = collection.get(
        where={"repo_id": repo_id},
        include=["documents", "metadatas"],
    )

    if not results or not results["documents"]:
        return {"error": "No data found for this repo"}

    combined = list(zip(results["documents"], results["metadatas"]))
    combined.sort(key=lambda x: x[1].get("timestamp_unix", 0))

    timeline = []
    for doc, meta in combined:
        files_str = meta.get("files_changed", "")
        files_list = [f.strip() for f in files_str.split(",") if f.strip()]
        additions = meta.get("additions", 0)
        deletions = meta.get("deletions", 0)
        
        msg = "No commit message"
        for line in doc.split("\n"):
            if line.startswith("Message: "):
                msg = line.replace("Message: ", "").strip()
                break

        imp_score = compute_importance(additions, deletions, files_list)
        arch_change = is_arch_change(files_list, additions, deletions)
        impact_type = classify_impact(arch_change, additions + deletions)

        timeline.append({
            "sha": meta.get("commit_sha", ""),
            "author": meta.get("author", "Unknown"),
            "date": meta.get("timestamp", "")[:10],
            "timestamp": meta.get("timestamp", ""),
            "timestamp_unix": meta.get("timestamp_unix", 0),
            "message": msg,
            "files": files_list,
            "additions": additions,
            "deletions": deletions,
            "importance_score": imp_score,
            "is_architecture_change": arch_change,
            "impact_type": impact_type,
            "explanation": f"Commit modified {len(files_list)} files (+{additions} / -{deletions} lines). Primary impact: {impact_type}.",
        })

    # Sample up to 20 commits evenly across the timeline for LLM summary
    step = max(1, -(-len(combined) // 20))  # ceiling division
    sampled = combined[::step][:20]
    context = "\n\n---\n\n".join([doc for doc, _ in sampled])
    prompt = evolution_prompt(repo_name, context)

    logger.info(f"Detecting evolution for {repo_name} ({len(sampled)} sampled commits)")
    try:
        narrative = await generate(prompt, system=SYSTEM_EVOLUTION)
    except Exception as e:
        logger.warning(f"Ollama generation fallback for evolution narrative: {e}")
        arch_count = sum(1 for t in timeline if t["is_architecture_change"])
        narrative = (
            f"### Architectural Evolution Summary for **{repo_name}**\n\n"
            f"- **Total Commits Analyzed:** {len(combined)}\n"
            f"- **Architectural Milestone Events:** {arch_count}\n"
            f"- **Sampled Milestones Analyzed:** {len(sampled)}\n\n"
            f"*(Local Ollama model connection unavailable. Complete commit timeline rendered with algorithmic impact scoring.)*"
        )

    return {
        "repo_id": repo_id,
        "repo_name": repo_name,
        "narrative": narrative,
        "timeline": timeline,
        "commits_analyzed": len(combined),
        "commits_sampled": len(sampled),
    }