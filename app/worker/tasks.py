import logging
from io import BytesIO
from PIL import Image

from app.api.client.minio import minio_client
from app.core.config import settings
from app.db import models
from app.db.session import SessionLocal
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="create_thumbnail_task")
def create_thumbnail_task(job_id: str):
    """
    Celery task to generate a 100x100 thumbnail for a given job.
    """
    logger.info(f"Worker received task for job_id: {job_id}")
    db = SessionLocal()  # Create a new database session for this task
    try:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database. Aborting task.")
            return

        original_image_data = minio_client.get_file(
            bucket_name=settings.MINIO_ORIGINALS_BUCKET,
            file_name=job_id
        )

        img = Image.open(BytesIO(original_image_data))
        img.thumbnail((100, 100))
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Save thumbnail back to MinIO
        minio_client.save_file(
            bucket_name=settings.MINIO_THUMBNAILS_BUCKET,
            file_name=job_id,
            data=buffer.getvalue()
        )

        # Update job status in the database to 'succeeded'
        job.status = "succeeded"
        job.thumbnail_filename = job_id
        db.commit()
        logger.info(f"Successfully processed and saved thumbnail for job_id: {job_id}")

    except Exception as e:
        logger.error(f"Task for job {job_id} failed: {e}", exc_info=True)
        job.status = "failed"
        db.commit()
    finally:
        db.close()