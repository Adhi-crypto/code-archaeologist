from datetime import datetime
import sys
import os
from pathlib import Path


# Force UTF-8 stdout encoding for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.temporal_rag.snapshot_store import get_collection
from app.temporal_rag.temporal_retriever import retrieve_temporal_context, build_temporal_context_string
from app.reasoning.causal_reasoner import classify_query_intent, compute_dynamic_confidence

BENCHMARK_QUERIES = [
    ("What is the repository about?", ["overview", "repo_summary", "README"]),
    ("Explain the project.", ["overview", "repo_summary", "README"]),
    ("Summarize repository evolution.", ["commit_snapshot", "evolution"]),
    ("What was the first commit?", ["commit_index:0", "Initial commit"]),
    ("Why was the second commit made?", ["commit_index:1"]),
    ("What does the second commit do?", ["commit_index:1"]),
    ("Who contributed most?", ["author", "commits"]),
    ("What files changed recently?", ["latest", "recent"]),
    ("Explain authentication module.", ["auth", "security", "token", "login"]),
    ("Explain database layer.", ["db", "database", "model", "schema", "sqlite"]),
]

def run_evaluation():
    collection = get_collection()
    count = collection.count()
    print("=" * 80)
    print("          CODE ARCHAEOLOGIST - RETRIEVAL EVALUATION BENCHMARK SUITE          ")
    print("=" * 80)
    print(f"ChromaDB Collection Vectors: {count}")

    if count == 0:
        print("\n[ERROR] Collection is empty. Ingest a repository first!")
        return

    # Grab active repo_id from collection
    sample = collection.get(limit=1, include=["metadatas"])
    if not sample or not sample.get("metadatas") or not sample["metadatas"]:
        print("\n[ERROR] Could not read metadata from collection.")
        return
    repo_id = sample["metadatas"][0].get("repo_id")
    repo_name = sample["metadatas"][0].get("repo_name", "Repository")

    # Ensure repo_summary document exists for active repo
    summary_id = f"{repo_id}_overview"
    sum_check = collection.get(ids=[summary_id], include=[])
    if not sum_check or not sum_check.get("ids"):
        print(f"Indexing missing repo_summary document for {repo_name} ({repo_id})...")
        from app.ingestion.git_ingestor import get_repo_path, read_overview_context
        from app.models.repo import RepoMetadata
        from app.temporal_rag.snapshot_store import store_commit_snapshots

        repo_path = get_repo_path(repo_id)
        overview_info = read_overview_context(repo_path)
        dummy_meta = RepoMetadata(
            repo_id=repo_id,
            repo_url="",
            repo_name=repo_name,
            branch="main",
            total_commits=count,
            languages=["Python", "JavaScript"],
            ingested_at=datetime.now(),

            status="ingested",
        )
        store_commit_snapshots(dummy_meta, [], overview_info)
        print("Indexed repo_summary document.")

    print(f"Target Repository ID: {repo_id} ({repo_name})\n")


    results_table = []
    total_score = 0

    for idx, (query, expected_keywords) in enumerate(BENCHMARK_QUERIES, 1):
        intent = classify_query_intent(query)
        contexts = retrieve_temporal_context(query, repo_id, n_results=5)
        match_score, confidence = compute_dynamic_confidence(contexts, query)
        prompt_ctx = build_temporal_context_string(contexts)

        # Grounding check: does context contain expected ground truth indicators?
        ctx_lower = prompt_ctx.lower()
        keyword_grounded = any(kw.lower() in ctx_lower for kw in expected_keywords)
        grounding_label = "EXCELLENT" if keyword_grounded and match_score > 60 else ("GOOD" if match_score >= 35 else "WEAK")

        total_score += match_score

        top_sha = contexts[0]["metadata"].get("commit_sha", "N/A") if contexts else "NONE"
        top_type = contexts[0]["metadata"].get("doc_type", "commit") if contexts else "NONE"

        print(f"Query {idx:2d}: '{query}'")
        print(f"  └─ Intent: {intent:14s} | Match Score: {match_score:2d}% | Conf: {confidence:2d}% | Grounding: {grounding_label}")
        print(f"  └─ Top Match: [{top_type}] SHA={top_sha} | Top Score={contexts[0]['relevance_score'] if contexts else 0}")
        print(f"  └─ Retrieved Snapshots: {len(contexts)} | Prompt Context Tokens: ~{len(prompt_ctx.split())}")
        print("-" * 80)

    avg_score = total_score / len(BENCHMARK_QUERIES)
    print("\n" + "=" * 80)
    print(f"EVALUATION SUMMARY | Average Evidence Match Score: {avg_score:.1f}%")
    print("=" * 80)

if __name__ == "__main__":
    run_evaluation()
