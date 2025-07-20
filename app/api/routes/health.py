import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db.session import engine
from app.api.client.minio import minio_client
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("health")
router = APIRouter()

@router.get("/healthz", tags=["Health Check"]) # Liveness
def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "message": "API is healthy"}

@router.get("/healthz/detailed", tags=["Health Check"]) # Readiness
def detailed_health_check():
    """Detailed health check with dependency status"""
    start_time = time.time()
    health_status = {
        "status": "ok",
        "timestamp": time.time(),
        "checks": {},
        "response_time_ms": 0
    }
    
    # Check database connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {"status": "healthy", "message": "Database connection successful"}
        logger.debug("Database health check passed")
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
        logger.error(f"Database health check failed: {e}")
    
    # Check MinIO connectivity
    try:
        buckets = minio_client.client.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        health_status["checks"]["storage"] = {
            "status": "healthy", 
            "message": "MinIO connection successful",
            "buckets": bucket_names
        }
        logger.debug("MinIO health check passed")
    except Exception as e:
        health_status["checks"]["storage"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
        logger.error(f"MinIO health check failed: {e}")
    
    # Check Redis connectivity (for Celery)
    try:
        from redis import Redis
        redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        redis_client.ping()
        health_status["checks"]["redis"] = {"status": "healthy", "message": "Redis connection successful"}
        logger.debug("Redis health check passed")
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
        logger.error(f"Redis health check failed: {e}")
    
    # Calculate response time
    health_status["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
    
    # Return appropriate HTTP status
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@router.get("/metrics", tags=["Monitoring"])
def get_metrics():
    """Basic application metrics"""
    try:
        from app.db import models
        from app.db.session import SessionLocal
        
        db = SessionLocal()
        try:
            # Get job statistics
            total_jobs = db.query(models.Job).count()
            processing_jobs = db.query(models.Job).filter(models.Job.status == "processing").count()
            succeeded_jobs = db.query(models.Job).filter(models.Job.status == "succeeded").count()
            failed_jobs = db.query(models.Job).filter(models.Job.status == "failed").count()
            
            return {
                "jobs": {
                    "total": total_jobs,
                    "processing": processing_jobs,
                    "succeeded": succeeded_jobs,
                    "failed": failed_jobs
                },
                "timestamp": time.time()
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")
