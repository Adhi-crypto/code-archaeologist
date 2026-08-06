import sys
import os
import asyncio
import time
from pathlib import Path

# Force UTF-8 encoding for Windows stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from app.temporal_rag.snapshot_store import get_collection
from app.reasoning.repository_intelligence import analyze_repository_intelligence
from app.reasoning.evolution_detector import detect_evolution
from app.reasoning.causal_reasoner import answer_repo_question, answer_repo_question_stream

async def run_pipeline_profiling():
    collection = get_collection()
    count = collection.count()

    print("=" * 80)
    print("      CODE ARCHAEOLOGIST - FULL PIPELINE PERFORMANCE PROFILING REPORT      ")
    print("=" * 80)
    print(f"Active ChromaDB Collection Vectors: {count}")

    if count == 0:
        print("[ERROR] No vectors in ChromaDB collection.")
        return

    sample = collection.get(limit=1, include=["metadatas"])
    if not sample or not sample.get("metadatas") or not sample["metadatas"]:
        print("[ERROR] Could not read metadata.")
        return
    repo_id = sample["metadatas"][0].get("repo_id")
    repo_name = sample["metadatas"][0].get("repo_name", "Repository")

    print(f"Target Repository ID: {repo_id} ({repo_name})\n")

    # 1. PROFILE REPOSITORY INTELLIGENCE PAGE
    print("-" * 80)
    print("1. PROFILING REPOSITORY INTELLIGENCE PAGE")
    print("-" * 80)
    
    t0 = time.perf_counter()
    intel_cold = await analyze_repository_intelligence(repo_id, repo_name, force_refresh=True)
    t_intel_cold = round((time.perf_counter() - t0) * 1000, 2)
    print(f"  └─ COLD Generation Latency : {t_intel_cold} ms | Health Score: {intel_cold.get('health_score')}/100")

    t1 = time.perf_counter()
    intel_warm = await analyze_repository_intelligence(repo_id, repo_name, force_refresh=False)
    t_intel_warm = round((time.perf_counter() - t1) * 1000, 2)
    print(f"  └─ WARM (Cached) Latency   : {t_intel_warm} ms [CACHE HIT]")

    # 2. PROFILE EVOLUTION TIMELINE PAGE
    print("\n" + "-" * 80)
    print("2. PROFILING EVOLUTION TIMELINE PAGE")
    print("-" * 80)

    t2 = time.perf_counter()
    evo_cold = await detect_evolution(repo_id, repo_name, force_refresh=True)
    t_evo_cold = round((time.perf_counter() - t2) * 1000, 2)
    print(f"  └─ COLD Timeline Generation: {t_evo_cold} ms | Analyzed: {evo_cold.get('commits_analyzed')} commits")

    t3 = time.perf_counter()
    evo_warm = await detect_evolution(repo_id, repo_name, force_refresh=False)
    t_evo_warm = round((time.perf_counter() - t3) * 1000, 2)
    print(f"  └─ WARM (Cached) Latency   : {t_evo_warm} ms [CACHE HIT]")

    # 3. PROFILE CHAT RAG & STREAMING PIPELINE
    print("\n" + "-" * 80)
    print("3. PROFILING CHAT RAG & STREAMING PIPELINE")
    print("-" * 80)

    test_queries = [
        "What is the repository about?",
        "Why was the second commit made?",
        "Explain authentication module.",
    ]

    for q in test_queries:
        print(f"\nQuery: '{q}'")
        t_stream_start = time.perf_counter()
        events = []
        async for sse_event in answer_repo_question_stream(q, repo_id, mode="chat"):
            events.append(sse_event)
        
        t_stream_total = round((time.perf_counter() - t_stream_start) * 1000, 2)

        meta_event = next((e for e in events if "event: metadata" in e), "")
        done_event = next((e for e in events if "event: done" in e), "")
        token_count = sum(1 for e in events if "event: token" in e)

        print(f"  └─ Stream Received Events : {len(events)} total SSE events | Tokens: {token_count}")
        print(f"  └─ Total Request Latency  : {t_stream_total} ms")
        if meta_event:
            print(f"  └─ Metadata Event Header  : {meta_event.strip()}")
        if done_event:
            print(f"  └─ Stream Done Latency    : {done_event.strip()}")

    print("\n" + "=" * 80)
    print("                   FULL PROFILING SUITE COMPLETED                   ")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_pipeline_profiling())
