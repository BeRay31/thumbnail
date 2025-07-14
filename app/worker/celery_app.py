from celery import Celery
from app.core.config import settings

redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

celery_app = Celery(
    "worker",
    broker=redis_url,
    backend=redis_url,  # Use Redis as the result backend as well
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
)