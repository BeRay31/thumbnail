import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import jobs, thumbnails, health
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.db.session import init_db

# Setup structured logging
setup_logging()
logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Thumbnail Service...")
    try:
        init_db()
        logger.info("✅ Database initialization completed")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise e
    
    yield  # Application is running
    logger.info("🛑 Shutting down Thumbnail Service...")

app = FastAPI(
    title="Cogent Labs Thumbnail API",
    description="API for creating and retrieving image thumbnails via background jobs.",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(thumbnails.router)