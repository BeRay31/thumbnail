import os
import psutil
import sys
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter(prefix="/debug", tags=["debug"])
logger = get_logger("debug")

@router.get("/info")
async def debug_info():
    """System debug info"""
    try:
        process = psutil.Process()
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "hostname": os.uname().nodename,
                "platform": sys.platform,
                "python": sys.version.split()[0],
                "pid": os.getpid(),
                "cwd": os.getcwd(),
            },
            "process": {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": round(process.memory_info().rss / 1024 / 1024, 1),
                "threads": process.num_threads(),
            },
            "config": settings.dict(),
        }
    except Exception as e:
        logger.error(f"Debug info failed: {e}")
        return {"error": str(e)}

@router.get("/database")
async def debug_database(db: Session = Depends(get_db)):
    """Check DB status"""
    try:
        db.execute(text("SELECT 1")).scalar()
        db_version = db.execute(text("SELECT version()")).scalar()
        
        job_stats = db.execute(text("""
            SELECT status, COUNT(*) as count
            FROM jobs GROUP BY status
        """)).fetchall()
        
        return {
            "connection": "ok",
            "version": db_version.split(" ")[0] if db_version else "unknown",
            "jobs": {row.status: row.count for row in job_stats},
        }
    except Exception as e:
        return {"connection": "failed", "error": str(e)}

@router.get("/redis")
async def debug_redis():
    """Check Redis status"""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        
        return {
            "connection": "ok",
            "queue_length": r.llen("celery"),
            "info": {k: v for k, v in r.info().items() if k in ["redis_version", "connected_clients", "used_memory_human"]},
        }
    except Exception as e:
        return {"connection": "failed", "error": str(e)}

@router.get("/minio")
async def debug_minio():
    """Check MinIO status"""
    try:
        from app.api.client.minio import get_minio_client
        client = get_minio_client()
        
        buckets = []
        for bucket in client.list_buckets():
            if bucket.name in ["originals", "thumbnails"]:
                objects = list(client.list_objects(bucket.name, recursive=True))
                buckets.append({
                    "name": bucket.name,
                    "objects": len(objects),
                    "size_mb": round(sum(obj.size or 0 for obj in objects) / 1024 / 1024, 1),
                })
        
        return {"connection": "ok", "buckets": buckets}
    except Exception as e:
        return {"connection": "failed", "error": str(e)}

@router.get("/config")
async def debug_config():
    """Get config (sanitized)"""
    config = settings.dict()
    
    # Hide secrets
    for key in list(config.keys()):
        if any(word in key.lower() for word in ["password", "secret", "key", "token"]):
            if config[key]:
                config[key] = "***"
    
    return config
