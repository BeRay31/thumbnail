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
    """
    Celery task to generate a 100x100 thumbnail for a given job.
    
    Args:
        job_id: The UUID of the job to process
        
    Returns:
        dict: Task result with status and details
    """
    # Create task-specific logger with job context
    logger = get_logger(f"celery.task.{job_id}")
    
    # Log task start with context
    logger.info(f"🎬 Starting thumbnail processing", extra={
        "job_id": job_id,
        "task_id": self.request.id,
        "retry_count": self.request.retries,
        "task_name": self.name
    })
    
    start_time = time.time()
    db = SessionLocal()
    job: Optional[models.Job] = None
    
    try:
        # Get job from database
        logger.debug(f"📋 Retrieving job from database")
        job = db.query(models.Job).filter(models.Job.id == job_id).first()
        if not job:
            error_msg = f"Job {job_id} not found in database"
            logger.error(error_msg, extra={"job_id": job_id, "error_type": "job_not_found"})
            return {"status": "failed", "error": error_msg}
        
        if job.status == "succeeded":
            logger.info(f"Job {job_id} has already been processed. Skipping.", extra={
                "job_id": job_id,
                "original_filename": job.original_filename,
                "status": job.status
            })
            return {"status": "succeeded", "message": "Job already processed"}
        
        logger.info(f"📄 Processing job for file: {job.original_filename}", extra={
            "job_id": job_id,
            "original_filename": job.original_filename,
            "current_status": job.status
        })
        
        # Update job status to processing (in case it wasn't set) -- let the users know that its being processed
        if job.status != "processing":
            job.status = "processing"
            db.commit()
            logger.info(f"📝 Updated job status to processing")

        logger.debug(f"📥 Downloading original image from MinIO bucket: {settings.MINIO_ORIGINALS_BUCKET}")
        try:
            original_image_data = minio_client.get_file(
                bucket_name=settings.MINIO_ORIGINALS_BUCKET,
                file_name=job_id
            )
            logger.debug(f"✅ Downloaded {len(original_image_data)} bytes from MinIO", extra={
                "job_id": job_id,
                "image_size_bytes": len(original_image_data)
            })
        except Exception as e:
            error_msg = f"Failed to download original image: {str(e)}"
            logger.error(error_msg, extra={
                "job_id": job_id,
                "error_type": "minio_download_failed",
                "bucket": settings.MINIO_ORIGINALS_BUCKET
            })
            raise Exception(error_msg)

        logger.debug(f"🖼️ Starting image processing")
        try:
            # Open and validate image
            img = Image.open(BytesIO(original_image_data))
            original_format = img.format
            original_mode = img.mode
            original_size = img.size
            
            logger.debug(f"📊 Original image info: format={original_format}, mode={original_mode}, size={original_size}")
            
            # Convert to RGB if necessary (handles RGBA, P mode, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                logger.debug(f"🔄 Converting image from {img.mode} to RGB")
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                logger.debug(f"🔄 Converting image from {img.mode} to RGB")
                img = img.convert('RGB')
            
            # Auto-orient image based on EXIF data
            img = ImageOps.exif_transpose(img)
            
            # Create thumbnail (100x100) maintaining aspect ratio
            img.thumbnail((100, 100), Image.Resampling.LANCZOS)
            thumbnail_size = img.size
            
            logger.info(f"🎨 Image resized from {original_size} to {thumbnail_size}", extra={
                "job_id": job_id,
                "original_size": original_size,
                "thumbnail_size": thumbnail_size,
                "original_format": original_format
            })
            
            buffer = BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)
            thumbnail_data = buffer.getvalue()
            
            logger.debug(f"💾 Thumbnail saved to buffer: {len(thumbnail_data)} bytes", extra={
                "job_id": job_id,
                "thumbnail_size_bytes": len(thumbnail_data)
            })
            
        except Exception as e:
            error_msg = f"Failed to process image: {str(e)}"
            logger.error(error_msg, extra={
                "job_id": job_id,
                "error_type": "image_processing_failed",
                "original_filename": job.original_filename
            }, exc_info=True)
            raise Exception(error_msg)

        logger.debug(f"📤 Uploading thumbnail to MinIO bucket: {settings.MINIO_THUMBNAILS_BUCKET}")
        try:
            minio_client.save_file(
                bucket_name=settings.MINIO_THUMBNAILS_BUCKET,
                file_name=job_id,
                data=thumbnail_data
            )
            logger.debug(f"✅ Thumbnail uploaded to MinIO successfully")
        except Exception as e:
            error_msg = f"Failed to upload thumbnail: {str(e)}"
            logger.error(error_msg, extra={
                "job_id": job_id,
                "error_type": "minio_upload_failed",
                "bucket": settings.MINIO_THUMBNAILS_BUCKET
            })
            raise Exception(error_msg)

        # Update job status to succeeded
        job.status = "succeeded"
        job.thumbnail_filename = job_id
        db.commit()
        
        processing_time = round(time.time() - start_time, 2)
        success_msg = f"Thumbnail processing completed successfully in {processing_time}s"
        
        logger.info(f"🎉 {success_msg}", extra={
            "job_id": job_id,
            "processing_time_seconds": processing_time,
            "original_size_bytes": len(original_image_data),
            "thumbnail_size_bytes": len(thumbnail_data),
            "compression_ratio": round(len(thumbnail_data) / len(original_image_data), 3)
        })
        
        return {
            "status": "succeeded", 
            "job_id": job_id, 
            "message": success_msg,
            "processing_time": processing_time,
            "original_size": len(original_image_data),
            "thumbnail_size": len(thumbnail_data)
        }

    except Exception as e:
        processing_time = round(time.time() - start_time, 2)
        error_msg = f"Task failed after {processing_time}s: {str(e)}"
        
        logger.error(f"💥 {error_msg}", extra={
            "job_id": job_id,
            "error_type": type(e).__name__,
            "processing_time_seconds": processing_time,
            "retry_count": self.request.retries,
            "max_retries": self.max_retries
        }, exc_info=True)
        
        # Update job status to failed if we have the job object
        if job:
            try:
                job.status = "failed"
                db.commit()
                logger.info(f"📝 Updated job status to failed in database")
            except Exception as db_error:
                logger.error(f"Failed to update job status to failed: {str(db_error)}", extra={
                    "job_id": job_id,
                    "error_type": "database_update_failed"
                })
        
        # Retry logic for transient errors
        if self.request.retries < self.max_retries:
            # Retry for specific types of errors
            retry_conditions = [
                "connection" in str(e).lower(),
                "timeout" in str(e).lower(),
                "network" in str(e).lower(),
                "temporarily unavailable" in str(e).lower()
            ]
            
            if any(retry_conditions):
                retry_delay = 60 * (2 ** self.request.retries)  # Exponential backoff
                logger.warning(f"🔄 Retrying job in {retry_delay}s (attempt {self.request.retries + 1}/{self.max_retries})", extra={
                    "job_id": job_id,
                    "retry_delay_seconds": retry_delay,
                    "retry_attempt": self.request.retries + 1,
                    "error_type": "transient_error"
                })
                raise self.retry(countdown=retry_delay)
        
        return {"status": "failed", "job_id": job_id, "error": error_msg}
        
    finally:
        db.close()
        logger.debug(f"🔒 Database session closed")