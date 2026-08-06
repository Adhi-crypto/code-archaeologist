import hashlib
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from loguru import logger
from app.core.config import settings

_model = None

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

@lru_cache(maxsize=1024)
def _cached_embed_by_hash(text_hash: str, text: str) -> tuple[float, ...]:
    model = get_embedding_model()
    return tuple(model.encode(text, normalize_embeddings=True).tolist())

def embed_text(text: str) -> list[float]:
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return list(_cached_embed_by_hash(text_hash, text))

def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    
    # Process texts using SHA256 hash lookup to reuse previously embedded texts
    results = [None] * len(texts)
    missing_indices = []
    missing_texts = []
    
    for i, text in enumerate(texts):
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        # Check LRU cache
        if _cached_embed_by_hash.cache_info().currsize > 0:
            try:
                # If cached, retrieving via function call will hit cache instantly
                vec = _cached_embed_by_hash(text_hash, text)
                results[i] = list(vec)
                continue
            except KeyError:
                pass
        missing_indices.append(i)
        missing_texts.append(text)
        
    if missing_texts:
        model = get_embedding_model()
        encoded = model.encode(missing_texts, normalize_embeddings=True, batch_size=32).tolist()
        for idx, text, emb in zip(missing_indices, missing_texts, encoded):
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            # Store in cache
            _cached_embed_by_hash(text_hash, text)
            results[idx] = emb

    return results