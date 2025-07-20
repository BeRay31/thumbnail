import os
from celery import Celery
from celery.signals import setup_logging, worker_ready, worker_shutdown
from app.core.config import settings

# Configure Celery app
redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

celery_app = Celery(
    "thumbnail_service",
    broker=redis_url,
    backend=redis_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Disable Celery's default logging to use custom logging
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Custom logging setup for Celery workers
@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Setup logging for Celery workers"""
    from app.core.logging import setup_logging as app_setup_logging, get_logger
    
    log_level = os.getenv("LOG_LEVEL", "INFO")
    app_setup_logging(level=log_level)
    
    logger = get_logger("celery.setup")
    logger.info(f"Celery worker logging configured with level: {log_level}")

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    from app.core.logging import get_logger
    logger = get_logger("celery.worker")
    logger.info(f"Celery worker {sender.hostname} ready")

@worker_shutdown.connect  
def worker_shutdown_handler(sender=None, **kwargs):
    from app.core.logging import get_logger
    logger = get_logger("celery.worker")
    logger.info(f"Celery worker {sender.hostname} shutting down")