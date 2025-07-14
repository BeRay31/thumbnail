import logging
from minio import Minio
from minio.error import S3Error, InvalidResponseError
from io import BytesIO
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("minio")

class MinioClient:
    def __init__(self):
        """Initialize MinIO client"""
        try:
            self.client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False
            )
            logger.info(f"MinIO client initialized: {settings.MINIO_ENDPOINT}")
            self.init_buckets()
        except Exception as e:
            logger.error(f"Failed to initialize MinIO: {str(e)}")
            raise

    def init_buckets(self):
        """Create buckets if they don't exist"""
        buckets = [settings.MINIO_ORIGINALS_BUCKET, settings.MINIO_THUMBNAILS_BUCKET]
        
        for bucket_name in buckets:
            try:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    logger.info(f"Created bucket: {bucket_name}")
                    
            except Exception as e:
                logger.error(f"Error with bucket {bucket_name}: {e}")
                raise

    def save_file(self, bucket_name: str, file_name: str, data: bytes):
        """Save file to MinIO bucket"""
        logger.info(f"Saving {file_name} to {bucket_name} ({len(data)} bytes)")
        
        try:
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=file_name,
                data=BytesIO(data),
                length=len(data),
                content_type='application/octet-stream'
            )
            logger.info(f"Saved {file_name} to {bucket_name}")
            
        except Exception as e:
            error_msg = f"Failed to save {file_name}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def get_file(self, bucket_name: str, file_name: str) -> bytes:
        """Get file from MinIO bucket"""
        logger.info(f"Getting {file_name} from {bucket_name}")
        response = None
        
        try:
            # Check if file exists
            try:
                self.client.stat_object(bucket_name, file_name)
            except S3Error as e:
                if e.code == 'NoSuchKey':
                    raise FileNotFoundError(f"File {file_name} not found")
                raise
            
            response = self.client.get_object(bucket_name, file_name)
            data = response.read()
            
            logger.info(f"Retrieved {file_name} ({len(data)} bytes)")
            return data
            
        except FileNotFoundError:
            raise
        except Exception as e:
            error_msg = f"Failed to get {file_name}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        finally:
            if response:
                response.close()
                response.release_conn()

try:
    minio_client = MinioClient()
except Exception as e:
    logger.error(f"Failed to create MinIO client: {e}")
    raise