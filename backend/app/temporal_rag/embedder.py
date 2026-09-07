from functools import lru_cache
import torch
from sentence_transformers import SentenceTransformer
from loguru import logger
from app.core.config import settings

_model = None
_device = None

def get_device() -> str:
    global _device
    if _device is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
    return _device

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        device = get_device()
        logger.info(f"Loading embedding model '{settings.EMBEDDING_MODEL}' on device: {device}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL, device=device)
    return _model

@lru_cache(maxsize=1024)
def _cached_embed(text: str) -> tuple[float, ...]:
    model = get_embedding_model()
    with torch.inference_mode():
        return tuple(model.encode(text, normalize_embeddings=True).tolist())

def embed_text(text: str) -> list[float]:
    return list(_cached_embed(text))

def embed_batch(texts: list[str], batch_size: int = 16) -> list[list[float]]:
    if not texts:
        return []
    model = get_embedding_model()
    with torch.inference_mode():
        return model.encode(texts, normalize_embeddings=True, batch_size=batch_size).tolist()