import time
from collections import defaultdict
from datetime import datetime
# pyrefly: ignore [missing-import]
from loguru import logger
from app.temporal_rag.snapshot_store import get_collection
from app.reasoning.ollama_client import generate
from app.reasoning.prompt_templates import SYSTEM_REPO_CHAT

SYSTEM_INTELLIGENCE_SUMMARY = """You are a Lead Software Architect & Repository Health Inspector.
Given automated repository analytics, write an executive technical summary (3-4 paragraphs) describing:
1. Repository activity & health state
2. Primary architectural hotspots and maintenance risks
3. Developer contribution patterns & technical debt
4. Actionable recommendations for software evolution and maintenance."""

_intelligence_cache: dict[str, dict] = {}


async def analyze_repository_intelligence(repo_id: str, repo_name: str = "Repository", force_refresh: bool = False) -> dict:
    if not force_refresh and repo_id in _intelligence_cache:
        logger.info(f"Returning cached Repository Intelligence for {repo_id}")
        return _intelligence_cache[repo_id]

    start_time = time.time()
    logger.info(f"Generating Repository Intelligence report for {repo_name} ({repo_id})")

    collection = get_collection()
    results = collection.get(
        where={"repo_id": repo_id},
        include=["documents", "metadatas"],
    )

    if not results or not results["documents"]:
        return {"error": "No ingested data found for this repository."}

    combined = list(zip(results["documents"], results["metadatas"]))
    combined.sort(key=lambda x: x[1].get("timestamp_unix", 0))

    total_commits = len(combined)

    # 1. Developer Analytics & Aggregations
    author_commits = defaultdict(int)
    file_change_counts = defaultdict(int)
    file_authors = defaultdict(set)
    file_churn = defaultdict(int)
    file_co_occurrences = defaultdict(int)
    
    total_additions = 0
    total_deletions = 0
    unique_files = set()
    timestamps = []

    arch_keywords = ["main", "config", "docker", "schema", "routes", "auth", "core", "api", "models", "pipeline"]

    for doc, meta in combined:
        author = meta.get("author", "Unknown")
        author_commits[author] += 1

        ts_unix = meta.get("timestamp_unix", 0)
        if ts_unix > 0:
            timestamps.append(ts_unix)

        additions = meta.get("additions", 0)
        deletions = meta.get("deletions", 0)
        total_additions += additions
        total_deletions += deletions

        files_str = meta.get("files_changed", "")
        files_list = [f.strip() for f in files_str.split(",") if f.strip()]
        unique_files.update(files_list)

        # File tracking
        for f in files_list:
            file_change_counts[f] += 1
            file_authors[f].add(author)
            file_churn[f] += (additions + deletions)

        # Co-evolving files tracking (pairs of files changed together in same commit)
        for i in range(len(files_list)):
            for j in range(i + 1, min(len(files_list), i + 6)):
                f1, f2 = sorted([files_list[i], files_list[j]])
                if f1 != f2:
                    file_co_occurrences[(f1, f2)] += 1

    # Statistics Calculation
    first_ts = min(timestamps) if timestamps else 0
    last_ts = max(timestamps) if timestamps else 0
    repo_age_days = max(1, (last_ts - first_ts) // (24 * 3600)) if first_ts and last_ts else 1
    repo_age_months = max(0.1, round(repo_age_days / 30.0, 1))

    avg_commits_per_month = round(total_commits / repo_age_months, 1)
    avg_commit_size = round((total_additions + total_deletions) / max(1, total_commits), 1)
    avg_files_modified = round(len(unique_files) / max(1, total_commits), 1)
    last_activity_date = datetime.fromtimestamp(last_ts).strftime("%Y-%m-%d") if last_ts else "Unknown"

    # Developer Analytics Array
    developers = []
    for author, count in sorted(author_commits.items(), key=lambda x: x[1], reverse=True):
        pct = round((count / total_commits) * 100.0, 1)
        developers.append({
            "author": author,
            "commits": count,
            "percentage": pct,
            "bus_factor_risk": "High" if pct > 50 else ("Medium" if pct > 25 else "Low")
        })

    bus_factor = sum(1 for d in developers if d["percentage"] >= 15)

    # Hotspot Detection Array
    hotspots = []
    for f, count in sorted(file_change_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
        authors_cnt = len(file_authors[f])
        is_arch = any(ak in f.lower() for ak in arch_keywords)
        
        # Risk level determination
        if count >= 8 and authors_cnt >= 3:
            risk = "Critical"
        elif count >= 5 or (is_arch and count >= 3):
            risk = "High"
        elif count >= 3:
            risk = "Medium"
        else:
            risk = "Low"

        hotspots.append({
            "file": f,
            "change_count": count,
            "authors_count": authors_cnt,
            "risk_level": risk,
            "total_churn": file_churn[f],
            "is_architecture": is_arch
        })

    # Co-Evolving Files Array
    co_evolving_files = []
    for (f1, f2), co_count in sorted(file_co_occurrences.items(), key=lambda x: x[1], reverse=True)[:10]:
        if co_count >= 2:
            co_evolving_files.append({
                "source": f1,
                "target": f2,
                "co_commit_count": co_count,
                "coupling_score": round(min(1.0, co_count / 5.0) * 100, 1)
            })

    # Health Score Calculation (0 - 100)
    # Factors: Dev distribution (25%), Churn stability (25%), Activity consistency (25%), File scope risk (25%)
    top_author_pct = developers[0]["percentage"] if developers else 100
    dev_health = max(0, 100 - (top_author_pct - 30) * 1.5) if top_author_pct > 30 else 95
    churn_health = max(30, 100 - min(70, (avg_commit_size / 400.0) * 70))
    activity_health = min(100, avg_commits_per_month * 5.0) if avg_commits_per_month > 1 else 60
    hotspot_health = max(30, 100 - (sum(1 for h in hotspots if h["risk_level"] in ["Critical", "High"]) * 8))

    health_score = round((dev_health * 0.25) + (churn_health * 0.25) + (activity_health * 0.25) + (hotspot_health * 0.25))
    health_score = max(25, min(98, health_score))

    if health_score >= 80:
        risk_level = "Low"
        recommendation = "Repository exhibits strong architectural health, balanced developer contributions, and controlled churn."
    elif health_score >= 60:
        risk_level = "Medium"
        recommendation = "Moderate repository risk. Monitor critical hotspots and distribute ownership across team members."
    else:
        risk_level = "High"
        recommendation = "High technical debt risk. Prioritize modular refactoring of top hotspots and improve developer bus factor."

    # Risk Assessment Metrics
    risk_assessment = {
        "technical_debt": round(max(15, min(95, 100 - churn_health))),
        "architecture_stability": round(max(20, min(98, hotspot_health))),
        "maintenance_risk": round(max(10, min(90, (100 - dev_health) * 0.8 + (100 - churn_health) * 0.2))),
        "bus_factor_score": bus_factor,
        "bug_risk": round(max(15, min(95, sum(1 for h in hotspots if h["risk_level"] == "Critical") * 25 + 15)))
    }

    # AI Summary Generation
    summary_prompt = (
        f"Generate an executive technical summary for repository '{repo_name}'.\n"
        f"ANALYTICS METRICS:\n"
        f"- Total Commits: {total_commits} | Authors: {len(developers)} | Files: {len(unique_files)}\n"
        f"- Repository Health Score: {health_score}/100 | Risk Level: {risk_level}\n"
        f"- Top Contributor Impact: {developers[0]['author']} ({developers[0]['percentage']}% of commits)\n"
        f"- Critical Hotspots Count: {sum(1 for h in hotspots if h['risk_level'] in ['Critical', 'High'])}\n"
        f"- Average Churn per Commit: +{total_additions} / -{total_deletions} total lines\n"
        f"Provide a clear executive summary detailing health state, primary hotspots, bus factor risks, and maintenance recommendations."
    )

    try:
        summary = await generate(summary_prompt, system=SYSTEM_INTELLIGENCE_SUMMARY)
    except Exception as e:
        logger.warning(f"Ollama generation fallback for repository intelligence summary: {e}")
        summary = (
            f"### Executive Intelligence Summary for **{repo_name}**\n\n"
            f"- **Repository Health Score:** **{health_score}/100** ({risk_level} Risk Level)\n"
            f"- **Activity Lifespan:** {total_commits} commits across {len(developers)} authors over {repo_age_months} months.\n"
            f"- **Primary Contributor:** `{developers[0]['author']}` ({developers[0]['percentage']}% of commits).\n"
            f"- **Critical Hotspots:** Identified {len(hotspots)} active file hotspots requiring maintenance attention.\n\n"
            f"**Recommendation:** {recommendation}"
        )

    analysis_time = round(time.time() - start_time, 2)

    res = {
        "health_score": health_score,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "summary": summary,
        "statistics": {
            "total_commits": total_commits,
            "total_authors": len(developers),
            "total_files": len(unique_files),
            "repo_age_days": repo_age_days,
            "repo_age_months": repo_age_months,
            "avg_commits_per_month": avg_commits_per_month,
            "avg_commit_size": avg_commit_size,
            "avg_files_modified": avg_files_modified,
            "last_activity_date": last_activity_date,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "net_churn": total_additions - total_deletions,
        },
        "developers": developers,
        "hotspots": hotspots,
        "co_evolving_files": co_evolving_files,
        "risk_assessment": risk_assessment,
        "analysis_time": analysis_time,
    }

    _intelligence_cache[repo_id] = res
    return res

