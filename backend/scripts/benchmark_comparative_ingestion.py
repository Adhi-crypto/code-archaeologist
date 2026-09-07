import sys
import time
from pathlib import Path
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion.git_ingestor import clone_or_pull, get_repo_id, get_repo_path, extract_commits, detect_languages, read_overview_context
from app.models.repo import RepoMetadata, CommitRecord
from app.temporal_rag.snapshot_store import get_collection, store_commit_snapshots
from app.temporal_rag.embedder import embed_batch, get_embedding_model

REPO_URL = "https://github.com/Adhi-crypto/code-archaeologist"
BRANCH = "main"

def benchmark_run(max_commits: int):
    print(f"\n=======================================================")
    print(f"BENCHMARKING INGESTION FOR {max_commits} COMMITS: {REPO_URL}")
    print(f"=======================================================")
    
    t_total_start = time.perf_counter()
    
    # 1. Clone / Pull
    t0 = time.perf_counter()
    repo_id = get_repo_id(REPO_URL)
    repo = clone_or_pull(REPO_URL, repo_id)
    t_clone_ms = round((time.perf_counter() - t0) * 1000, 2)
    print(f"1. Clone / Pull Time                : {t_clone_ms} ms")

    # 2. Extract Commits & Diff Stats
    t1 = time.perf_counter()
    commits = extract_commits(repo, BRANCH, max_commits=max_commits)
    t_commits_ms = round((time.perf_counter() - t1) * 1000, 2)
    print(f"2. Commit Parsing & Diff Extraction: {t_commits_ms} ms ({len(commits)} commits parsed)")

    # 3. Language Detection & Overview Reading
    t2 = time.perf_counter()
    languages = detect_languages(repo)
    repo_path = get_repo_path(repo_id)
    overview_info = read_overview_context(repo_path)
    t_overview_ms = round((time.perf_counter() - t2) * 1000, 2)
    print(f"3. Languages & Overview Analysis    : {t_overview_ms} ms (Langs: {languages[:4]})")

    # Build Metadata
    repo_name = REPO_URL.rstrip("/").split("/")[-1].replace(".git", "")
    metadata = RepoMetadata(
        repo_id=repo_id,
        repo_url=REPO_URL,
        repo_name=repo_name,
        branch=BRANCH,
        total_commits=len(commits),
        languages=languages,
        ingested_at=datetime.now(),
        status="ingested",
    )

    # 4. Snapshot Storage (Embedding + ChromaDB Indexing)
    # We clear the existing collection records for this repo so we measure fresh embedding & indexing
    collection = get_collection()
    try:
        collection.delete(where={"repo_id": repo_id})
    except Exception:
        pass

    stage_timings = {}
    def progress_cb(stage_msg, current, total):
        pass

    t3 = time.perf_counter()
    # Explicitly measure embedding and upsert
    from app.temporal_rag.snapshot_store import build_commit_document
    documents = []
    metadatas = []
    ids = []
    
    # Overview doc
    summary_id = f"{repo_id}_overview"
    summary_doc = f"Repository Overview: {repo_name}\nPrimary Languages: {', '.join(languages)}"
    documents.append(summary_doc)
    metadatas.append({
        "repo_id": repo_id,
        "repo_name": repo_name,
        "doc_type": "repo_summary",
        "commit_sha": "overview",
        "timestamp": metadata.ingested_at.isoformat(),
        "timestamp_unix": int(metadata.ingested_at.timestamp()),
        "commit_index": -1,
        "total_commits": len(commits),
    })
    ids.append(summary_id)

    for i, commit in enumerate(commits):
        doc = build_commit_document(commit, repo_id, repo_name)
        documents.append(doc)
        metadatas.append({
            "repo_id": repo_id,
            "repo_name": repo_name,
            "doc_type": "commit_snapshot",
            "commit_sha": commit.sha,
            "author": commit.author,
            "timestamp": commit.timestamp.isoformat(),
            "timestamp_unix": int(commit.timestamp.timestamp()),
            "files_changed": ",".join(commit.files_changed[:10]),
            "additions": commit.additions,
            "deletions": commit.deletions,
            "commit_index": i,
            "total_commits": len(commits),
        })
        ids.append(f"{repo_id}_{commit.sha}")

    t_emb_start = time.perf_counter()
    embeddings = embed_batch(documents, batch_size=16)
    t_embed_ms = round((time.perf_counter() - t_emb_start) * 1000, 2)
    print(f"4. Embedding Generation Time       : {t_embed_ms} ms ({len(documents)} snapshots embedded)")

    t_chroma_start = time.perf_counter()
    chunk_size = 200
    for start in range(0, len(ids), chunk_size):
        end = start + chunk_size
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )
    t_chroma_ms = round((time.perf_counter() - t_chroma_start) * 1000, 2)
    print(f"5. ChromaDB Indexing / Upsert Time : {t_chroma_ms} ms ({len(ids)} documents indexed)")

    t_total_ms = round((time.perf_counter() - t_total_start) * 1000, 2)
    print(f"-------------------------------------------------------")
    print(f"TOTAL INGESTION PIPELINE TIME       : {t_total_ms} ms ({t_total_ms/1000:.3f} s)")
    print(f"=======================================================")

    return {
        "max_commits": max_commits,
        "actual_commits": len(commits),
        "clone_ms": t_clone_ms,
        "commit_parsing_ms": t_commits_ms,
        "overview_ms": t_overview_ms,
        "embed_ms": t_embed_ms,
        "chroma_ms": t_chroma_ms,
        "total_ms": t_total_ms,
    }

if __name__ == "__main__":
    # Warm up models
    get_embedding_model()
    get_collection()

    runs = []
    for count in [10, 50, 100]:
        r = benchmark_run(count)
        runs.append(r)

    print("\n\n" + "=" * 95)
    print("                      COMPARATIVE INGESTION BENCHMARK RESULTS")
    print("=" * 95)
    print(f"{'Max Commits':<12} | {'Actual':<8} | {'Git Parse':<12} | {'Embed':<12} | {'ChromaDB':<12} | {'Total Ingestion':<16}")
    print("-" * 95)
    for r in runs:
        print(f"{r['max_commits']:<12} | {r['actual_commits']:<8} | {r['commit_parsing_ms']:>8.1f} ms | {r['embed_ms']:>8.1f} ms | {r['chroma_ms']:>8.1f} ms | {r['total_ms']:>10.1f} ms ({r['total_ms']/1000:.2f}s)")
    print("=" * 95)
