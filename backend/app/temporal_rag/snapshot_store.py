import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger
from datetime import datetime
from app.core.config import settings
from app.models.repo import CommitRecord, RepoMetadata
from app.temporal_rag.embedder import embed_text, embed_batch

_client = None
_collection = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def build_commit_document(commit: CommitRecord, repo_id: str, repo_name: str) -> str:
    """Build a rich text document for each commit snapshot — this is what gets embedded."""
    return f"""Repository: {repo_name}
Commit: {commit.sha}
Author: {commit.author}
Date: {commit.timestamp.strftime('%Y-%m-%d')}
Message: {commit.message}
Files changed: {', '.join(commit.files_changed[:10])}
Changes: +{commit.additions} -{commit.deletions} lines
Summary: {commit.diff_summary}"""


def store_commit_snapshots(metadata: RepoMetadata, commits: list[CommitRecord], overview_info: dict = None):
    """Store all commits as time-stamped embeddings in ChromaDB, skipping already indexed SHAs."""
    collection = get_collection()
    repo_id = metadata.repo_id
    repo_name = metadata.repo_name

    logger.info(f"Checking existing snapshots in ChromaDB for {repo_name}")

    documents = []
    metadatas = []
    ids = []

    # Store or update the dedicated repo_summary document
    if overview_info:
        summary_id = f"{repo_id}_overview"
        summary_doc = f"""Repository Overview: {repo_name}
Primary Languages: {', '.join(metadata.languages)}
Total Commits: {len(commits)}
Directory Structure & Entry Points:
{overview_info.get('file_tree', '')}

README Content & Documentation:
{overview_info.get('readme', '')}

Key Project Dependencies:
{overview_info.get('dependencies', '')}"""

        summary_meta = {
            "repo_id": repo_id,
            "repo_name": repo_name,
            "doc_type": "repo_summary",
            "commit_sha": "overview",
            "timestamp": metadata.ingested_at.isoformat(),
            "timestamp_unix": int(metadata.ingested_at.timestamp()),
            "commit_index": -1,
            "total_commits": len(commits),
        }
        documents.append(summary_doc)
        metadatas.append(summary_meta)
        ids.append(summary_id)

    # Query existing commit IDs to avoid re-embedding
    target_ids = [f"{repo_id}_{c.sha}" for c in commits]
    existing_ids = set()
    try:
        existing_res = collection.get(ids=target_ids, include=[])
        if existing_res and existing_res.get("ids"):
            existing_ids = set(existing_res["ids"])
    except Exception as e:
        logger.warning(f"Could not query existing IDs in Chroma: {e}")

    skipped_count = 0
    for i, commit in enumerate(commits):
        c_id = f"{repo_id}_{commit.sha}"
        if c_id in existing_ids:
            skipped_count += 1
            continue

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
        ids.append(c_id)

    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} already indexed commits for {repo_name}")

    if not ids:
        logger.info(f"All {len(commits)} commits are already fully indexed for {repo_name}.")
        return

    # Batch embed missing documents
    embeddings = embed_batch(documents)

    # Batch upsert into ChromaDB in chunks of 100
    chunk_size = 100
    for start in range(0, len(ids), chunk_size):
        end = start + chunk_size
        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

    logger.success(f"Stored {len(ids)} new snapshots (including overview) in ChromaDB for {repo_name}")




def get_collection_stats(repo_id: str) -> dict:
    collection = get_collection()
    results = collection.get(where={"repo_id": repo_id}, limit=1)
    count = collection.count()
    return {"total_documents": count, "repo_id": repo_id}