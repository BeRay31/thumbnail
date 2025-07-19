from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import jobs, thumbnails, health, debug
from app.core.logging import setup_logging, get_logger
from app.db.session import init_db

setup_logging()
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    try:
        init_db()
        logger.info("DB ready")
    except Exception as e:
        logger.error(f"DB init failed: {e}")
        raise
    
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="Thumbnail Service",
    description="Generate thumbnails from uploaded images",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(thumbnails.router)
app.include_router(debug.router)