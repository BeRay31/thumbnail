import logging
import logging.config
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import jobs, thumbnails
from app.core.config import settings
from app.db.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application
    """
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

@app.get("/healthz", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "API is healthy"}

app.include_router(jobs.router, tags=["Thumbnail Jobs"])
app.include_router(thumbnails.router, tags=["Thumbnail Jobs"])