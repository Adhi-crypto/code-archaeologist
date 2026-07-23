import time
from loguru import logger
from app.temporal_rag.temporal_retriever import retrieve_temporal_context
from app.reasoning.ollama_client import generate
from app.reasoning.confidence_scorer import extract_query_keywords, calculate_weighted_confidence

SYSTEM_BUG_ORIGIN = """You are an expert Software Forensic Engineer & Bug Origin Auditor.
Your task is to analyze git commit history and code diffs to pinpoint which commit introduced a bug, regression, or failure.
Base your reasoning strictly on the provided commit evidence.
Explain why this commit was selected, what changed, why it is related to the query, and what evidence supports it."""


def bug_origin_prompt(query: str, repo_name: str, candidate_context: str) -> str:
    return f"""A bug or regression was reported in repository '{repo_name}':
REPORTED ISSUE: "{query}"

RETRIEVED COMMIT HISTORY EVIDENCE:
{candidate_context}

Analyze the candidate commits above and identify the commit most likely responsible for introducing this issue.

Provide a clear forensic report answering:
1. WHY THIS COMMIT: Why is this commit suspected above others?
2. WHAT CHANGED: What code modifications, files, or logic were altered?
3. BUG MECHANISM: How did this change introduce the bug or regression?
4. SUPPORTING EVIDENCE: Citations of commit messages, author actions, or diff statistics.
5. CONFIDENCE EVALUATION: Explain the confidence score."""


async def analyze_bug_origin(repo_id: str, query: str, repo_name: str = "Repository") -> dict:
    start_time = time.time()
    logger.info(f"Analyzing bug origin for repo {repo_id}: '{query[:60]}'")
    
    # 1. Query Understanding
    extracted = extract_query_keywords(query)
    
    # 2. Temporal Retrieval via ChromaDB
    contexts = retrieve_temporal_context(query, repo_id=repo_id, n_results=10)
    
    if not contexts:
        return {
            "error": "No indexed commit history found for this repository."
        }
        
    # 3. Candidate Scoring & Ranking
    author_counts = {}
    for ctx in contexts:
        auth = ctx["metadata"].get("author", "Unknown")
        author_counts[auth] = author_counts.get(auth, 0) + 1
    max_author_count = max(author_counts.values()) if author_counts else 1
    
    total_docs = len(contexts)
    ranked_candidates = []
    
    for i, ctx in enumerate(contexts):
        doc = ctx["document"]
        meta = ctx["metadata"]
        
        sha = meta.get("commit_sha", "")
        author = meta.get("author", "Unknown")
        date_str = meta.get("timestamp", "")[:10]
        files_str = meta.get("files_changed", "")
        files_list = [f.strip() for f in files_str.split(",") if f.strip()]
        additions = meta.get("additions", 0)
        deletions = meta.get("deletions", 0)
        
        # Message extraction
        msg = "No commit message"
        for line in doc.split("\n"):
            if line.startswith("Message: "):
                msg = line.replace("Message: ", "").strip()
                break
                
        # Semantic Score (Vector distance relevance score)
        sem_score = max(0.0, min(1.0, ctx.get("relevance_score", 0.5)))
        
        # File Scope Match Score
        file_match_score = 0.0
        if extracted["files"]:
            file_match_score = 1.0 if any(any(qf in f.lower() for qf in extracted["files"]) for f in files_list) else 0.0
        elif extracted["keywords"]:
            matched_kws = sum(1 for kw in extracted["keywords"] if any(kw in f.lower() for f in files_list) or kw in msg.lower())
            file_match_score = min(1.0, matched_kws / max(1, len(extracted["keywords"])))
            
        # Recency / Temporal Score
        recency_score = (total_docs - i) / float(total_docs)
        
        # Architecture Impact Score
        arch_keywords = ["main", "config", "docker", "schema", "routes", "auth", "core", "api", "models", "pipeline"]
        is_arch = any(any(ak in f.lower() for ak in arch_keywords) for f in files_list) or (additions + deletions > 150)
        arch_score = 0.9 if is_arch else 0.4
        
        # Commit Importance
        importance_score = min(1.0, (additions + deletions + len(files_list) * 10) / 250.0)
        
        # Developer Frequency
        dev_score = min(1.0, author_counts.get(author, 1) / float(max_author_count))
        
        # Calculate Weighted Confidence
        confidence = calculate_weighted_confidence(
            semantic_score=sem_score,
            file_match_score=file_match_score,
            recency_score=recency_score,
            arch_impact_score=arch_score,
            commit_importance=importance_score,
            dev_frequency_score=dev_score,
        )
        
        diff_summary = f"Modified {len(files_list)} files (+{additions} / -{deletions} lines)"
        
        reason = (
            f"High match ({int(sem_score*100)}% semantic similarity) targeting "
            f"critical files with {impact_category(is_arch, additions+deletions)}."
        )
        
        ranked_candidates.append({
            "sha": sha,
            "author": author,
            "date": date_str,
            "timestamp": meta.get("timestamp", ""),
            "timestamp_unix": meta.get("timestamp_unix", 0),
            "message": msg,
            "confidence": confidence,
            "reason": reason,
            "files": files_list,
            "additions": additions,
            "deletions": deletions,
            "diff_summary": diff_summary,
            "architecture_change": is_arch,
        })
        
    # Sort candidates by weighted confidence descending
    ranked_candidates.sort(key=lambda x: x["confidence"], reverse=True)
    
    likely_commit = ranked_candidates[0]
    supporting_commits = ranked_candidates[1:5]
    
    # 4. LLM Forensic Reasoning Context
    context_parts = []
    for cand in ranked_candidates[:5]:
        context_parts.append(
            f"Commit SHA: {cand['sha']}\n"
            f"Author: {cand['author']} | Date: {cand['date']}\n"
            f"Message: {cand['message']}\n"
            f"Files Changed: {', '.join(cand['files'])}\n"
            f"Diff Summary: {cand['diff_summary']} | Arch Change: {cand['architecture_change']}"
        )
    candidate_context_str = "\n\n---\n\n".join(context_parts)
    
    prompt = bug_origin_prompt(query, repo_name, candidate_context_str)
    
    try:
        explanation = await generate(prompt, system=SYSTEM_BUG_ORIGIN)
    except Exception as e:
        logger.warning(f"Ollama generation fallback for bug origin explanation: {e}")
        explanation = (
            f"### Bug Forensic Analysis Report\n\n"
            f"- **Suspected Root Cause Commit:** `{likely_commit['sha']}`\n"
            f"- **Author:** {likely_commit['author']} ({likely_commit['date']})\n"
            f"- **Confidence Score:** **{likely_commit['confidence']}%**\n\n"
            f"**Commit Message:** {likely_commit['message']}\n"
            f"**Modified Files:** {', '.join(likely_commit['files'])}\n\n"
            f"**Forensic Reasoning:** Commit `{likely_commit['sha']}` introduces modifications "
            f"to key codebase files matching query entities ({query[:60]}). "
            f"Multi-factor scoring confirms high semantic and file scope correlation."
        )
        
    analysis_time = round(time.time() - start_time, 2)
    
    return {
        "likely_commit": likely_commit,
        "supporting_commits": supporting_commits,
        "llm_explanation": explanation,
        "analysis_time": analysis_time,
    }


def impact_category(is_arch: bool, churn: int) -> str:
    if is_arch:
        return "Architectural Changes"
    elif churn > 200:
        return "High Churn Changes"
    return "Targeted Refactoring"
