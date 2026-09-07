import time
import asyncio
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


def _sync_build_evolution_timeline(repo_id: str) -> tuple[list[dict], list, int]:
    collection = get_collection()

    results = collection.get(
        where={"repo_id": repo_id},
        include=["documents", "metadatas"],
    )

    if not results or not results["documents"]:
        return [], [], 0

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

    return timeline, sampled, len(combined)


_evolution_cache: dict[str, dict] = {}
_timeline_cache: dict[str, tuple] = {}

def invalidate_evolution_cache(repo_id: str = None):
    global _evolution_cache, _timeline_cache
    if repo_id:
        if repo_id in _evolution_cache:
            del _evolution_cache[repo_id]
        if repo_id in _timeline_cache:
            del _timeline_cache[repo_id]
        logger.info(f"[CACHE INVALIDATED] Evolution cache cleared for repo {repo_id}")
    else:
        _evolution_cache.clear()
        _timeline_cache.clear()
        logger.info("[CACHE INVALIDATED] All evolution caches cleared")

def get_deterministic_timeline(repo_id: str) -> tuple[list[dict], list[dict], int]:
    """Return deterministic timeline events in <10ms without LLM synthesis."""
    if repo_id in _timeline_cache:
        return _timeline_cache[repo_id]
    timeline, sampled, total_count = _sync_build_evolution_timeline(repo_id)
    if timeline:
        _timeline_cache[repo_id] = (timeline, sampled, total_count)
    return timeline, sampled, total_count

async def detect_evolution(repo_id: str, repo_name: str, force_refresh: bool = False) -> dict:
    if not force_refresh and repo_id in _evolution_cache:
        logger.info(f"[CACHE HIT] Returning cached Evolution Timeline for repo {repo_id}")
        return _evolution_cache[repo_id]

    logger.info(f"[CACHE MISS] Building Evolution Timeline for {repo_name} ({repo_id})")
    t_start = time.perf_counter()

    timeline, sampled, total_count = await asyncio.to_thread(get_deterministic_timeline, repo_id)

    if not timeline:
        return {"error": "No data found for this repo"}

    # Compress commit context: extract structural milestone signals instead of raw snapshot documents
    step = max(1, -(-len(timeline) // 15))
    sampled_events = timeline[::step][:15]
    milestone_lines = []
    for evt in sampled_events:
        files_preview = ", ".join(evt["files"][:4]) if evt["files"] else "various"
        milestone_lines.append(
            f"- [{evt['date']}] {evt['sha']} ({evt['author']}): \"{evt['message']}\" "
            f"| Impact: {evt['impact_type']} (+{evt['additions']}/-{evt['deletions']}) | Files: {files_preview}"
        )
    context = "\n".join(milestone_lines)
    prompt = evolution_prompt(repo_name, context)

    logger.info(f"Detecting evolution narrative for {repo_name} ({len(sampled_events)} compressed milestones)")
    try:
        narrative = await generate(prompt, system=SYSTEM_EVOLUTION, num_predict=384)
    except Exception as e:
        logger.warning(f"Ollama generation fallback for evolution narrative: {e}")
        arch_count = sum(1 for t in timeline if t["is_architecture_change"])
        narrative = (
            f"### Architectural Evolution Summary for **{repo_name}**\n\n"
            f"- **Total Commits Analyzed:** {total_count}\n"
            f"- **Architectural Milestone Events:** {arch_count}\n"
            f"- **Sampled Milestones Analyzed:** {len(sampled_events)}\n\n"
            f"*(Local Ollama model connection unavailable. Complete commit timeline rendered with algorithmic impact scoring.)*"
        )

    t_total = round((time.perf_counter() - t_start) * 1000, 2)
    logger.info(f"Evolution Timeline Generation Complete for {repo_id} in {t_total}ms")

    res = {
        "repo_id": repo_id,
        "repo_name": repo_name,
        "narrative": narrative,
        "timeline": timeline,
        "commits_analyzed": total_count,
        "commits_sampled": len(sampled_events),
        "execution_time_ms": t_total,
    }

    _evolution_cache[repo_id] = res
    return res
