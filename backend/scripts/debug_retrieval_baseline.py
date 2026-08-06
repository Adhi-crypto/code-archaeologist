import sys
import os
from pathlib import Path

# Force UTF-8 encoding for Windows stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from loguru import logger
from app.temporal_rag.snapshot_store import get_collection
from app.temporal_rag.embedder import embed_text
from app.temporal_rag.temporal_retriever import retrieve_temporal_context, build_temporal_context_string
from app.reasoning.causal_reasoner import classify_query_intent

def run_diagnostics():
    collection = get_collection()
    count = collection.count()
    print("=" * 70)
    print("      CODE ARCHAEOLOGIST - RETRIEVAL DIAGNOSTIC BASELINE      ")
    print("=" * 70)
    print(f"1. ChromaDB Collection Count: {count} total vectors")
    
    if count == 0:
        print("\n[WARNING] Collection is empty. Ingest a repository first!")
        return

    # 2. Inspect raw sample document
    print("\n" + "-" * 70)
    print("2. Raw Sample Document Content (1st stored document in ChromaDB):")
    print("-" * 70)
    sample_res = collection.get(limit=1, include=["documents", "metadatas"])
    if sample_res and sample_res.get("documents") and sample_res["documents"]:
        print(f"ID: {sample_res['ids'][0]}")
        print(f"Metadata: {sample_res['metadatas'][0]}")
        print(f"Document Snippet:\n{sample_res['documents'][0][:300]}...")
    else:
        print("No sample document returned.")

    # 3. Test Raw Query Vector Searches & Distance Distributions
    test_queries = [
        "What is this repository about?",
        "Explain the project.",
        "What does the second commit do?",
        "What was the first commit?",
        "Summarize repository evolution.",
    ]

    print("\n" + "-" * 70)
    print("3. Testing Raw Vector Search & Raw Distances:")
    print("-" * 70)

    for q in test_queries:
        intent = classify_query_intent(q)
        q_emb = embed_text(q)
        raw_res = collection.query(
            query_embeddings=[q_emb],
            n_results=5,
            include=["documents", "metadatas", "distances"],
        )
        print(f"\nQUERY: '{q}' [Intent: {intent}]")
        if raw_res and raw_res["distances"] and raw_res["distances"][0]:
            for rank, (dist, doc_id, meta, doc) in enumerate(zip(
                raw_res["distances"][0],
                raw_res["ids"][0],
                raw_res["metadatas"][0],
                raw_res["documents"][0],
            ), 1):
                msg_line = next((l.replace("Message: ", "") for l in doc.split("\n") if l.startswith("Message: ")), doc[:40])
                print(f"  Rank {rank}: Dist={dist:.4f} | ID={doc_id} | SHA={meta.get('commit_sha','')} | Msg='{msg_line[:40]}'")
        else:
            print("  No results returned.")

    # 4. Inspect Context Builder & Prompt Context
    print("\n" + "-" * 70)
    print("4. Context Builder Prompt Output Sample:")
    print("-" * 70)
    sample_query = test_queries[0]
    sample_repo_id = sample_res['metadatas'][0].get("repo_id") if sample_res and sample_res.get("metadatas") else ""
    if sample_repo_id:
        retrieved_contexts = retrieve_temporal_context(sample_query, sample_repo_id, n_results=5)
        prompt_ctx = build_temporal_context_string(retrieved_contexts)
        print(f"Retrieved {len(retrieved_contexts)} contexts for '{sample_query}':")
        print(prompt_ctx[:500] + "\n...")

    print("\n=" * 70)
    print("                      END OF DIAGNOSTICS                      ")
    print("=" * 70)

if __name__ == "__main__":
    run_diagnostics()
