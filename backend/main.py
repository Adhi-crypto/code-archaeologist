from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import repo, chat, evolution, analysis

setup_logging(debug=settings.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Ollama model : {settings.OLLAMA_MODEL}")
    logger.info(f"ChromaDB     : {settings.CHROMA_DB_PATH}")
    yield
    logger.info("Shutting down.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repo.router,      prefix="/api/repo",      tags=["Repository"])
app.include_router(repo.router,      prefix="/api/repository",tags=["Repository"])
app.include_router(chat.router,      prefix="/api/chat",      tags=["Chat"])
app.include_router(evolution.router, prefix="/api/evolution", tags=["Evolution"])
app.include_router(analysis.router,  prefix="/api/analysis",  tags=["Analysis"])
app.include_router(analysis.router,  prefix="/api/bug-origin",tags=["Bug Origin"])



@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}