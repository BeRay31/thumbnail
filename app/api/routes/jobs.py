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
    """Submit an image for thumbnail generation"""
    logger.info(f"Processing upload: {image.filename}")
    
    try:
        validate_image_file(image)
        
        new_job = db_models.Job(status="processing", original_filename=image.filename)
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        logger.info(f"Created job {new_job.id}")

        # Save original image
        try:
            image_data = image.file.read()
            minio_client.save_file(
                bucket_name=settings.MINIO_ORIGINALS_BUCKET,
                file_name=str(new_job.id),
                data=image_data,
            )
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            db.delete(new_job)
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to save uploaded image")

        # Queue thumbnail generation
        try:
            create_thumbnail_task.delay(str(new_job.id))
            logger.info(f"Queued job {new_job.id}")
        except Exception as e:
            logger.error(f"Failed to queue job: {str(e)}")
            new_job.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to queue thumbnail generation")

        return new_job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/jobs/{job_id}", response_model=job_schemas.JobStatusResponse, tags=["Thumbnail Jobs"])
def get_job_status(job_id: UUID, db: Session = Depends(get_db)):
    """Get job status by ID"""
    logger.info(f"Getting status for job {job_id}")
    
    try:
        job = db.query(db_models.Job).filter(db_models.Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/jobs", response_model=list[job_schemas.JobStatusResponse], tags=["Thumbnail Jobs"])
def list_jobs(skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    """List all jobs"""
    logger.info(f"Listing jobs (skip={skip}, limit={limit})")
    
    try:
        skip, limit = validate_pagination_params(skip, limit)
        jobs = db.query(db_models.Job)\
                .order_by(db_models.Job.created_at.desc())\
                .offset(skip)\
                .limit(limit)\
                .all()
        
        return jobs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")