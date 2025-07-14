import logging
from uuid import UUID
from fastapi import (APIRouter, Depends, File, HTTPException, Response, UploadFile)
from sqlalchemy.orm import Session
from app.api.client.minio import minio_client
from app.api.schemas import job as job_schemas
from app.core.config import settings
from app.db import models as db_models
from app.db.session import get_db
from app.worker.tasks import create_thumbnail_task

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/jobs", response_model=job_schemas.JobCreateResponse, status_code=202, tags=["Thumbnail Jobs"])
def submit_job(
    image: UploadFile = File(..., description="Image file to be thumbnailed."),
    db: Session = Depends(get_db),
):
    logger.info(f"Received job submission for file: {image.filename}")
    
    new_job = db_models.Job(status="processing", original_filename=image.filename)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    image_data = image.file.read()
    minio_client.save_file(
        bucket_name=settings.MINIO_ORIGINALS_BUCKET,
        file_name=str(new_job.id),
        data=image_data,
    )

    # Dispatch the thumbnailing task to Celery
    create_thumbnail_task.delay(str(new_job.id))
    logger.info(f"Successfully dispatched job {new_job.id} to worker.")

    return new_job

@router.get("/jobs/{job_id}", response_model=job_schemas.JobStatusResponse, tags=["Thumbnail Jobs"],)
def get_job_status(job_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieves the current status of a specific job.
    """
    logger.info(f"Fetching status for job {job_id}")
    job = db.query(db_models.Job).filter(db_models.Job.id == job_id).first()
    if not job:
        logger.warning(f"Job {job_id} not found.")
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/jobs", response_model=list[job_schemas.JobStatusResponse], tags=["Thumbnail Jobs"])
def list_jobs(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """
    Lists all submitted jobs with pagination.
    """
    logger.info(f"Listing jobs with skip={skip}, limit={limit}")
    jobs = db.query(db_models.Job).offset(skip).limit(limit).all()
    return jobs