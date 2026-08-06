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


from concurrent.futures import ThreadPoolExecutor

def _process_single_commit(commit) -> CommitRecord | None:
    try:
        files_changed = list(commit.stats.files.keys()) if commit.stats else []
        additions = commit.stats.total.get("insertions", 0) if commit.stats else 0
        deletions = commit.stats.total.get("deletions", 0) if commit.stats else 0

        diff_summary = _build_diff_summary(files_changed, additions, deletions)

        return CommitRecord(
            sha=commit.hexsha[:10],
            message=commit.message.strip(),
            author=str(commit.author),
            timestamp=datetime.fromtimestamp(commit.committed_date),
            files_changed=files_changed[:20],
            additions=additions,
            deletions=deletions,
            diff_summary=diff_summary,
        )
    except Exception as e:
        logger.warning(f"Skipping commit {commit.hexsha[:8]}: {e}")
        return None

def extract_commits(repo: Repo, branch: str = "main", max_commits: int = 500) -> list[CommitRecord]:
    logger.info(f"Extracting up to {max_commits} commits from branch: {branch}")

    try:
        commit_iter = list(repo.iter_commits(branch, max_count=max_commits))
    except Exception:
        commit_iter = list(repo.iter_commits(max_count=max_commits))

    # Parallelize commit stats & diff extraction across thread pool
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(_process_single_commit, commit_iter))

    commits = [c for c in results if c is not None]
    logger.info(f"Extracted {len(commits)} commits (parallelized)")
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


def read_overview_context(repo_path: Path) -> dict:
    """Reads README, dependency files, and top-level directory tree for deterministic repo overview context."""
    readme_text = ""
    for fname in ["README.md", "README.rst", "README.txt", "readme.md", "README"]:
        r_file = repo_path / fname
        if r_file.exists():
            try:
                readme_text = r_file.read_text(encoding="utf-8", errors="ignore")[:2500]
                break
            except Exception:
                pass

    deps_text = ""
    for dfname in ["package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "pom.xml", "go.mod"]:
        d_file = repo_path / dfname
        if d_file.exists():
            try:
                deps_text += f"\n--- {dfname} ---\n" + d_file.read_text(encoding="utf-8", errors="ignore")[:1000]
            except Exception:
                pass

    # Top-level directory tree
    tree_lines = []
    try:
        for item in sorted(repo_path.iterdir()):
            if item.name.startswith(".") or item.name in ["__pycache__", "node_modules", "venv", ".venv"]:
                continue
            item_type = "DIR " if item.is_dir() else "FILE"
            tree_lines.append(f"  [{item_type}] {item.name}")
    except Exception:
        pass
    file_tree = "\n".join(tree_lines[:30])

    return {
        "readme": readme_text.strip(),
        "dependencies": deps_text.strip(),
        "file_tree": file_tree.strip(),
    }


def ingest_repo(repo_url: str, branch: str = "main", max_commits: int = 500) -> tuple[RepoMetadata, list[CommitRecord], dict]:
    repo_id = get_repo_id(repo_url)
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")

    repo = clone_or_pull(repo_url, repo_id)
    repo_path = get_repo_path(repo_id)
    commits = extract_commits(repo, branch, max_commits)
    languages = detect_languages(repo)
    overview_info = read_overview_context(repo_path)

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
    return metadata, commits, overview_info