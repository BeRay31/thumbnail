import logging
from uuid import UUID
from fastapi import (APIRouter, Depends, File, HTTPException, Response, UploadFile)
from sqlalchemy.orm import Session
from app.api.client.minio import minio_client
from app.api.schemas import job as job_schemas
from app.core.config import settings
from app.core.validation import validate_image_file, validate_pagination_params
from app.core.logging import get_logger
from app.db import models as db_models
from app.db.session import get_db
from app.worker.tasks import create_thumbnail_task

logger = get_logger("jobs")
router = APIRouter()

@router.post("/jobs", response_model=job_schemas.JobCreateResponse, status_code=202, tags=["Thumbnail Jobs"])
def submit_job(
    image: UploadFile = File(..., description="Image file to be thumbnailed."),
    db: Session = Depends(get_db),
):
    """
    Submit an image for thumbnail generation
    
    - Accepts various image formats (JPEG, PNG, GIF, WebP, BMP, TIFF)
    - Maximum file size: 50MB
    - Returns job ID for status tracking
    """
    logger.info(f"Received job submission for file: {image.filename}")
    
    try:
        # Validate uploaded image
        validate_image_file(image)
        new_job = db_models.Job(status="processing", original_filename=image.filename)
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        logger.info(f"Created job {new_job.id} for file: {image.filename}")

        try:
            image_data = image.file.read()
            minio_client.save_file(
                bucket_name=settings.MINIO_ORIGINALS_BUCKET,
                file_name=str(new_job.id),
                data=image_data,
            )
            logger.info(f"Saved original image for job {new_job.id} to MinIO")
        except Exception as e:
            logger.error(f"Failed to save image for job {new_job.id}: {str(e)}")
            db.delete(new_job)
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to save uploaded image")

        # Dispatch the thumbnailing task to Celery
        try:
            create_thumbnail_task.delay(str(new_job.id))
            logger.info(f"Successfully dispatched job {new_job.id} to worker.")
        except Exception as e:
            logger.error(f"Failed to dispatch job {new_job.id} to worker: {str(e)}")
            new_job.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to queue thumbnail generation job")

        return new_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in job submission: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during job submission")

@router.get("/jobs/{job_id}", response_model=job_schemas.JobStatusResponse, tags=["Thumbnail Jobs"])
def get_job_status(job_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieve the current status of a specific job
    
    - Returns job details including status, timestamps, and filenames
    - Status can be: "processing", "succeeded", or "failed"
    """
    logger.info(f"Fetching status for job {job_id}")
    
    try:
        job = db.query(db_models.Job).filter(db_models.Job.id == job_id).first()
        if not job:
            logger.warning(f"Job {job_id} not found.")
            raise HTTPException(status_code=404, detail="Job not found")
        
        logger.debug(f"Retrieved job {job_id} with status: {job.status}")
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/jobs", response_model=list[job_schemas.JobStatusResponse], tags=["Thumbnail Jobs"])
def list_jobs(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    """
    List all submitted jobs with pagination
    
    - Use skip and limit parameters for pagination
    - Returns jobs ordered by creation date (newest first)
    - Maximum limit is 1000 jobs per request
    """
    logger.info(f"Listing jobs with skip={skip}, limit={limit}")
    
    try:
        skip, limit = validate_pagination_params(skip, limit)
        jobs = db.query(db_models.Job)\
                .order_by(db_models.Job.created_at.desc())\
                .offset(skip)\
                .limit(limit)\
                .all()
        
        logger.debug(f"Retrieved {len(jobs)} jobs")
        return jobs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")