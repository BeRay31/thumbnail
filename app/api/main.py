import logging
import logging.config

from fastapi import FastAPI

from app.api.routes import jobs, thumbnails
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cogent Labs Thumbnail API",
    description="API for creating and retrieving image thumbnails via background jobs.",
    version="1.0.0",
)
@app.get("/healthz", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "API is healthy"}
app.include_router(jobs.router, tags=["Thumbnail Jobs"])
app.include_router(thumbnails.router, tags=["Thumbnail Jobs"])