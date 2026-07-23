from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Code Archaeologist"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "deepseek-coder-v2"
    OLLAMA_TIMEOUT: int = 120

    # ChromaDB
    CHROMA_DB_PATH: str = str(BASE_DIR / "data" / "chroma_db")
    CHROMA_COLLECTION_NAME: str = "repo_snapshots"

    # Repos clone path
    REPOS_PATH: str = str(BASE_DIR / "data" / "repos")

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # GitHub (optional, for PR/issue fetching)
    GITHUB_TOKEN: str = ""

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()