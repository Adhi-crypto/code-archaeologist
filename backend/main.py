import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import repo, chat, evolution, analysis
from app.temporal_rag.embedder import get_embedding_model
from app.temporal_rag.snapshot_store import get_collection
from app.reasoning.ollama_client import warmup_ollama

setup_logging(debug=settings.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Ollama model : {settings.OLLAMA_MODEL}")
    logger.info(f"ChromaDB     : {settings.CHROMA_DB_PATH}")
    
    # Pre-warm heavy singletons on startup to prevent cold-start penalties
    logger.info("Pre-warming embedding model, ChromaDB client & Ollama LLM...")
    get_embedding_model()
    get_collection()
    await warmup_ollama()
    logger.info("Startup warm-up complete.")
    
    yield
    logger.info("Shutting down application...")
    from app.temporal_rag.snapshot_store import close_chroma_client
    close_chroma_client()
    logger.info("Application shutdown complete.")



app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Gzip compression for payloads larger than 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for latency profiling & X-Process-Time header
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    if settings.DEBUG:
        logger.debug(f"{request.method} {request.url.path} processed in {process_time:.4f}s")
    return response

app.include_router(repo.router,      prefix="/api/repo",      tags=["Repository"])
app.include_router(repo.router,      prefix="/api/repository",tags=["Repository"])
app.include_router(chat.router,      prefix="/api/chat",      tags=["Chat"])
app.include_router(evolution.router, prefix="/api/evolution", tags=["Evolution"])
app.include_router(analysis.router,  prefix="/api/analysis",  tags=["Analysis"])
app.include_router(analysis.router,  prefix="/api/bug-origin",tags=["Bug Origin"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}