import logging
from io import BytesIO
from PIL import Image, ImageOps
from typing import Optional
import time

from app.api.client.minio import minio_client
from app.core.config import settings
from app.db import models
from app.db.session import SessionLocal
from app.worker.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger("tasks")

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def create_thumbnail_task(self, job_id: str):
    """Generate 100x100 thumbnail"""
    logger.info(f"Processing job {job_id}")
    start_time = time.time()
    db = SessionLocal()
    
    try:
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"status": "failed", "error": "Job not found"}
        
        if job.status == "succeeded":
            logger.info(f"Job {job_id} already done")
            return {"status": "succeeded"}
        
        logger.info(f"Processing {job.original_filename}")
        
        # Set to processing
        job.status = "processing"
        db.commit()

        # Get original
        original_data = minio_client.get_file(
            bucket_name=settings.MINIO_ORIGINALS_BUCKET,
            file_name=job_id
        )
        logger.debug(f"Got {len(original_data)} bytes")

        # Process image
        img = Image.open(BytesIO(original_data))
        original_size = img.size
        
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Create thumbnail
        img = ImageOps.exif_transpose(img)
        img.thumbnail((100, 100), Image.Resampling.LANCZOS)
        
        logger.info(f"Resized from {original_size} to {img.size}")
        
        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)
        thumbnail_data = buffer.getvalue()

        # Upload thumbnail
        try:
            minio_client.save_file(
                bucket_name=settings.MINIO_THUMBNAILS_BUCKET,
                file_name=job_id,
                data=thumbnail_data
            )
        except Exception as e:
            error_msg = f"Failed to upload thumbnail: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Update job status
        job.status = "succeeded"
        job.thumbnail_filename = job_id
        db.commit()
        
        processing_time = round(time.time() - start_time, 2)
        logger.info(f"Completed in {processing_time}s")
        
        return {
            "status": "succeeded", 
            "job_id": job_id, 
            "processing_time": processing_time
        }

    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        logger.error(f"Failed after {elapsed}s: {e}")
        
        if 'job' in locals() and job:
            try:
                job.status = "failed"
                db.commit()
            except Exception:
                pass
        
        # Retry if we haven't hit max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()