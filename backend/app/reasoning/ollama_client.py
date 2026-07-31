import httpx
from loguru import logger
from app.core.config import settings


async def generate(prompt: str, system: str = "") -> str:
    """
    Calls local Ollama REST API to generate text responses.
    Logs structured execution telemetry and raises detailed RuntimeErrors on failure.
    """
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 1024},
    }
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    logger.info(f"[LLM START] Provider: Ollama | Model: {settings.OLLAMA_MODEL} | URL: {url} | Prompt Chars: {len(prompt)}")

    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            res_json = response.json()
            answer = res_json.get("response", "").strip()
            logger.info(f"[LLM SUCCESS] Model: {settings.OLLAMA_MODEL} | Response Chars: {len(answer)}")
            return answer
    except httpx.ConnectError as e:
        logger.error(
            f"[LLM CONNECT FAILURE] Unable to reach Ollama daemon at {settings.OLLAMA_BASE_URL}.\n"
            f"Provider: Ollama | Model: {settings.OLLAMA_MODEL}\n"
            f"Error: {e}",
            exc_info=True
        )
        raise RuntimeError(
            f"Ollama connection refused at {settings.OLLAMA_BASE_URL}. "
            f"Please verify Ollama is running locally ('ollama serve')."
        ) from e
    except httpx.HTTPStatusError as e:
        logger.error(
            f"[LLM HTTP ERROR] Ollama returned HTTP {e.response.status_code}.\n"
            f"Model Requested: {settings.OLLAMA_MODEL}\n"
            f"Response Body: {e.response.text}",
            exc_info=True
        )
        raise RuntimeError(
            f"Ollama model error (HTTP {e.response.status_code}): {e.response.text}. "
            f"Please verify model '{settings.OLLAMA_MODEL}' is pulled ('ollama pull {settings.OLLAMA_MODEL}')."
        ) from e
    except Exception as e:
        logger.error(
            f"[LLM UNEXPECTED ERROR] Generation failed for model '{settings.OLLAMA_MODEL}': {type(e).__name__}: {e}",
            exc_info=True
        )
        raise RuntimeError(f"Ollama LLM generation error ({type(e).__name__}): {str(e)}") from e