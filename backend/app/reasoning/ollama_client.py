import time
import re
import hashlib
from functools import lru_cache
import httpx
from loguru import logger
from app.core.config import settings

_llm_cache: dict[str, str] = {}

# Single shared persistent HTTP client with keep-alive connection pooling
_client: httpx.AsyncClient | None = None

def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.OLLAMA_TIMEOUT, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
        )
    return _client

def _cache_key(prompt: str, system: str) -> str:
    raw = f"{system}:::{prompt}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

async def warmup_ollama() -> bool:
    """Pre-warms the configured Ollama LLM model in GPU VRAM with keep_alive: 60m."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": "ping",
        "stream": False,
        "keep_alive": "60m",
        "options": {"num_predict": 1},
    }
    try:
        client = get_http_client()
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
        )
        if response.status_code == 200:
            logger.info(f"Ollama model '{settings.OLLAMA_MODEL}' pre-warmed successfully (keep_alive=60m).")
            return True
    except Exception as e:
        logger.warning(f"Ollama pre-warm ping failed (model will load on demand): {e}")
    return False

def invalidate_llm_cache():
    global _llm_cache
    _llm_cache.clear()
    logger.info("[CACHE INVALIDATED] Ollama LLM cache cleared")

DEFAULT_OPTIONS = {
    "temperature": 0.2,
    "top_k": 40,
    "top_p": 0.9,
    "num_ctx": 4096,
    "num_batch": 256,
}

async def generate(prompt: str, system: str = "", num_predict: int = 512, options: dict = None) -> str:
    merged_options = {**DEFAULT_OPTIONS, "num_predict": num_predict}
    if options:
        merged_options.update(options)

    key = _cache_key(f"{prompt}:::options={merged_options}", system)
    if key in _llm_cache:
        logger.info(f"[CACHE HIT] Returning cached Ollama LLM response (Prompt Key: {key[:12]})")
        return _llm_cache[key]

    logger.info(f"[CACHE MISS] Invoking Ollama LLM model '{settings.OLLAMA_MODEL}' (Prompt Key: {key[:12]}, num_predict={merged_options['num_predict']})")
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "keep_alive": "60m",
        "options": merged_options,
    }
    t_start = time.perf_counter()
    try:
        client = get_http_client()
        logger.info(f"[OLLAMA REQUEST SENT] POST {settings.OLLAMA_BASE_URL}/api/generate")
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
        )
        t_recv = time.perf_counter()
        logger.info(f"[OLLAMA RESPONSE RECEIVED] HTTP status {response.status_code} in {round((t_recv - t_start) * 1000, 2)}ms")
        response.raise_for_status()
        result = response.json().get("response", "").strip()
        if result:
            _llm_cache[key] = result
        return result
    except Exception as e:
        logger.error(f"Ollama generation failed after {round((time.perf_counter() - t_start) * 1000, 2)}ms: {e}")
        raise RuntimeError(f"LLM unavailable: {e}")

async def generate_stream(prompt: str, system: str = "", num_predict: int = 512, options: dict = None):
    """Async generator streaming LLM tokens in real-time from Ollama."""
    merged_options = {**DEFAULT_OPTIONS, "num_predict": num_predict}
    if options:
        merged_options.update(options)

    key = _cache_key(f"{prompt}:::options={merged_options}", system)
    if key in _llm_cache:
        logger.info(f"[CACHE HIT] Streaming cached Ollama LLM response (Prompt Key: {key[:12]})")
        yield _llm_cache[key]
        return

    logger.info(f"[CACHE MISS] Initiating Ollama LLM stream for '{settings.OLLAMA_MODEL}' (Prompt Key: {key[:12]}, num_predict={merged_options['num_predict']})")
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": True,
        "keep_alive": "60m",
        "options": merged_options,
    }
    full_response = []
    t_start = time.perf_counter()
    t_first_byte = None
    try:
        client = get_http_client()
        logger.info(f"[OLLAMA STREAM REQUEST SENT] POST {settings.OLLAMA_BASE_URL}/api/generate (stream=True)")
        async with client.stream(
            "POST",
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                if t_first_byte is None:
                    t_first_byte = time.perf_counter()
                    logger.info(f"[OLLAMA FIRST BYTE RECEIVED] TTFT latency: {round((t_first_byte - t_start) * 1000, 2)}ms")
                import json
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        full_response.append(token)
                        yield token
                    if chunk.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
        
        t_last_byte = time.perf_counter()
        logger.info(f"[OLLAMA LAST BYTE RECEIVED] Total stream time: {round((t_last_byte - t_start) * 1000, 2)}ms | Tokens: {len(full_response)}")
        cached_str = "".join(full_response).strip()
        if cached_str:
            _llm_cache[key] = cached_str
    except Exception as e:
        logger.error(f"Ollama stream generation failed after {round((time.perf_counter() - t_start) * 1000, 2)}ms: {e}")
        raise RuntimeError(f"LLM streaming unavailable: {e}")