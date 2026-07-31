import os
import hashlib
from pathlib import Path
from datetime import datetime
from loguru import logger
from git import Repo, GitCommandError
from app.core.config import settings
from app.models.repo import CommitRecord, RepoMetadata


def get_repo_id(repo_url: str) -> str:
    return hashlib.md5(repo_url.encode()).hexdigest()[:12]


def get_repo_path(repo_id: str) -> Path:
    return Path(settings.REPOS_PATH) / repo_id


def clone_or_pull(repo_url: str, repo_id: str) -> Repo:
    repo_path = get_repo_path(repo_id)
    if repo_path.exists():
        logger.info(f"Repo already cloned, pulling latest: {repo_id}")
        repo = Repo(repo_path)
        repo.remotes.origin.pull()
    else:
        logger.info(f"Cloning repo: {repo_url}")
        repo_path.mkdir(parents=True, exist_ok=True)
        repo = Repo.clone_from(repo_url, repo_path)
    return repo


def extract_commits(repo: Repo, branch: str = "main", max_commits: int = 500) -> list[CommitRecord]:
    logger.info(f"Extracting up to {max_commits} commits from branch: {branch}")
    commits = []

    try:
        commit_iter = list(repo.iter_commits(branch, max_count=max_commits))
    except Exception:
        commit_iter = list(repo.iter_commits(max_count=max_commits))

    for commit in commit_iter:
        try:
            files_changed = list(commit.stats.files.keys()) if commit.stats else []
            additions = commit.stats.total.get("insertions", 0) if commit.stats else 0
            deletions = commit.stats.total.get("deletions", 0) if commit.stats else 0

            diff_summary = _build_diff_summary(files_changed, additions, deletions)

            commits.append(CommitRecord(
                sha=commit.hexsha[:10],
                message=commit.message.strip(),
                author=str(commit.author),
                timestamp=datetime.fromtimestamp(commit.committed_date),
                files_changed=files_changed[:20],
                additions=additions,
                deletions=deletions,
                diff_summary=diff_summary,
            ))
        except Exception as e:
            logger.warning(f"Skipping commit {commit.hexsha[:8]}: {e}")
            continue

    logger.info(f"Extracted {len(commits)} commits")
    return commits


def _build_diff_summary(files: list[str], additions: int, deletions: int) -> str:
    if not files:
        return ""
    file_list = ", ".join(files[:5])
    suffix = f" (+{len(files)-5} more)" if len(files) > 5 else ""
    return f"Changed: {file_list}{suffix} | +{additions} -{deletions}"


def detect_languages(repo: Repo) -> list[str]:
    extensions = {}
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".java": "Java", ".go": "Go", ".rs": "Rust", ".cpp": "C++",
        ".c": "C", ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
    }
    try:
        for item in repo.tree().traverse():
            if hasattr(item, "path"):
                ext = Path(item.path).suffix.lower()
                if ext in ext_map:
                    lang = ext_map[ext]
                    extensions[lang] = extensions.get(lang, 0) + 1
    except Exception:
        pass
    return sorted(extensions, key=extensions.get, reverse=True)


def ingest_repo(repo_url: str, branch: str = "main", max_commits: int = 500) -> tuple[RepoMetadata, list[CommitRecord]]:
    repo_id = get_repo_id(repo_url)
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")

    repo = clone_or_pull(repo_url, repo_id)
    commits = extract_commits(repo, branch, max_commits)
    languages = detect_languages(repo)

    metadata = RepoMetadata(
        repo_id=repo_id,
        repo_url=repo_url,
        repo_name=repo_name,
        branch=branch,
        total_commits=len(commits),
        languages=languages,
        ingested_at=datetime.now(),
        status="ingested",
    )

    logger.info(f"Ingestion complete: {repo_name} | {len(commits)} commits | langs: {languages}")
    return metadata, commits