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

@router.post("/jobs", response_model=job_schemas.JobCreateResponse, status_code=202)
def submit_job(image: UploadFile = File(...), db: Session = Depends(get_db)):
    """Submit image for thumbnailing"""
    logger.info(f"Got upload: {image.filename}")
    
    validate_image_file(image)
    
    job = db_models.Job(status="processing", original_filename=image.filename)
    db.add(job)
    db.commit()
    db.refresh(job)
    
    logger.info(f"Created job {job.id}")

    # Save original
    try:
        image_data = image.file.read()
        minio_client.save_file(
            bucket_name=settings.MINIO_ORIGINALS_BUCKET,
            file_name=str(job.id),
            data=image_data,
        )
    except Exception as e:
        logger.error(f"Failed to save: {e}")
        db.delete(job)
        db.commit()
        raise HTTPException(status_code=500, detail="Upload failed")

    # Queue task
    try:
        create_thumbnail_task.delay(str(job.id))
        logger.info(f"Queued job {job.id}")
    except Exception as e:
        logger.error(f"Queue failed: {e}")
        job.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail="Task queue failed")

    return job

@router.get("/jobs/{job_id}", response_model=job_schemas.JobStatusResponse)
def get_job_status(job_id: UUID, db: Session = Depends(get_db)):
    """Get job by ID"""
    job = db.query(db_models.Job).filter(db_models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/jobs", response_model=list[job_schemas.JobStatusResponse])
def list_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List jobs"""
    validate_pagination_params(skip, limit)
    return db.query(db_models.Job).order_by(db_models.Job.created_at.desc()).offset(skip).limit(limit).all()

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