import httpx
from loguru import logger
from app.core.config import settings


async def generate(prompt: str, system: str = "") -> str:
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 1024},
    }
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama generation failed: {e}")
        raise RuntimeError(f"LLM unavailable: {e}")