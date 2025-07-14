import logging
from fastapi import FastAPI

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,  # Set the minimum level of messages to log
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cogent Labs Thumbnail API",
    description="API for creating and retrieving image thumbnails via background jobs.",
    version="1.0.0"
)

@app.get("/healthz", tags=["Health Check"])
def health_check(): # Kube health check endpoint
    return {"status": "ok", "message": "API is healthy"}