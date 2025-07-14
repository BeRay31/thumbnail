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

# Base logger for this module
base_logger = get_logger("celery.tasks")

@celery_app.task(name="create_thumbnail_task", bind=True, max_retries=3, default_retry_delay=60)
def create_thumbnail_task(self, job_id: str):
    """Generate a 100x100 thumbnail for a given job"""
    logger = get_logger(f"celery.task.{job_id}")
    
    logger.info(f"Starting thumbnail processing for job {job_id}")
    start_time = time.time()
    db = SessionLocal()
    job: Optional[models.Job] = None
    
    try:
        # Get job from database
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            error_msg = f"Job {job_id} not found"
            logger.error(error_msg)
            return {"status": "failed", "error": error_msg}
        
        if job.status == "succeeded":
            logger.info(f"Job {job_id} already processed")
            return {"status": "succeeded", "message": "Job already processed"}
        
        logger.info(f"Processing {job.original_filename}")
        
        # Update status to processing
        if job.status != "processing":
            job.status = "processing"
            db.commit()

        # Download original image
        try:
            original_image_data = minio_client.get_file(
                bucket_name=settings.MINIO_ORIGINALS_BUCKET,
                file_name=job_id
            )
            logger.debug(f"Downloaded {len(original_image_data)} bytes")
        except Exception as e:
            error_msg = f"Failed to download image: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Process image
        try:
            img = Image.open(BytesIO(original_image_data))
            original_size = img.size
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Auto-orient and create thumbnail
            img = ImageOps.exif_transpose(img)
            img.thumbnail((100, 100), Image.Resampling.LANCZOS)
            
            logger.info(f"Resized from {original_size} to {img.size}")
            
            # Save to buffer
            buffer = BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)
            thumbnail_data = buffer.getvalue()
            
        except Exception as e:
            error_msg = f"Image processing failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

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
        processing_time = round(time.time() - start_time, 2)
        error_msg = f"Task failed after {processing_time}s: {str(e)}"
        
        logger.error(error_msg)
        
        # Update job status to failed
        if job:
            try:
                job.status = "failed"
                db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update job status: {str(db_error)}")
        
        # Retry for network-related errors
        if self.request.retries < self.max_retries:
            retry_conditions = [
                "connection" in str(e).lower(),
                "timeout" in str(e).lower(),
                "network" in str(e).lower()
            ]
            
            if any(retry_conditions):
                retry_delay = 60 * (2 ** self.request.retries)
                logger.warning(f"Retrying in {retry_delay}s")
                raise self.retry(countdown=retry_delay)
        
        return {"status": "failed", "job_id": job_id, "error": error_msg}
        
    finally:
        db.close()