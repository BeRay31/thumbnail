import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.api.client.minio import minio_client
from app.core.config import settings
from app.db import models as db_models
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/thumbnails/{job_id}", tags=["Thumbnails"])
def get_thumbnail(job_id: UUID, db: Session = Depends(get_db)):
    """Get thumbnail image by id"""
    logger.info(f"Attempting to retrieve thumbnail for job {job_id}")
    job = db.query(db_models.Job).filter(db_models.Job.id == job_id).first()

    if not job:
        logger.warning(f"Job {job_id} not found for thumbnail retrieval.")
        raise HTTPException(status_code=404, detail="Job not found.")

    if job.status != "succeeded":
        logger.warning(
            f"Thumbnail for job {job_id} requested but status is '{job.status}'."
        )
        raise HTTPException(
            status_code=404, detail="Thumbnail not ready or job failed."
        )

    thumbnail_data = minio_client.get_file(
        bucket_name=settings.MINIO_THUMBNAILS_BUCKET, file_name=str(job.id)
    )

    return Response(content=thumbnail_data, media_type="image/png")