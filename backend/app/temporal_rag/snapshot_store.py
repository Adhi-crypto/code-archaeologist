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


def store_commit_snapshots(metadata: RepoMetadata, commits: list[CommitRecord]):
    """Store all commits as time-stamped embeddings in ChromaDB."""
    collection = get_collection()
    repo_id = metadata.repo_id
    repo_name = metadata.repo_name

    logger.info(f"Storing {len(commits)} commit snapshots for {repo_name}")

    documents = []
    embeddings = []
    metadatas = []
    ids = []

    for i, commit in enumerate(commits):
        doc = build_commit_document(commit, repo_id, repo_name)
        documents.append(doc)
        metadatas.append({
            "repo_id": repo_id,
            "repo_name": repo_name,
            "commit_sha": commit.sha,
            "author": commit.author,
            "timestamp": commit.timestamp.isoformat(),
            "timestamp_unix": int(commit.timestamp.timestamp()),
            "files_changed": ",".join(commit.files_changed[:10]),
            "additions": commit.additions,
            "deletions": commit.deletions,
            "commit_index": i,       # 0 = most recent
            "total_commits": len(commits),
        })
        ids.append(f"{repo_id}_{commit.sha}")

    # Batch embed
    embeddings = embed_batch(documents)

    # Upsert into ChromaDB (safe to re-run)
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.success(f"Stored {len(commits)} snapshots in ChromaDB for {repo_name}")


def get_collection_stats(repo_id: str) -> dict:
    collection = get_collection()
    results = collection.get(where={"repo_id": repo_id}, limit=1)
    count = collection.count()
    return {"total_documents": count, "repo_id": repo_id}