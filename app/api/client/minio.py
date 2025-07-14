import logging
from minio import Minio
from minio.error import S3Error, InvalidResponseError
from io import BytesIO
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("minio")

class MinioClient:
    def __init__(self):
        """Initialize MinIO client with connection and bucket setup"""
        try:
            self.client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=False
            )
            logger.info(f"MinIO client initialized for endpoint: {settings.MINIO_ENDPOINT}")
            self.init_buckets()
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise

    def init_buckets(self):
        """Initialize required buckets, creating them if they don't exist"""
        buckets_to_create = [
            settings.MINIO_ORIGINALS_BUCKET,
            settings.MINIO_THUMBNAILS_BUCKET
        ]
        
        for bucket_name in buckets_to_create:
            try:
                if not self.client.bucket_exists(bucket_name):
                    logger.info(f"Bucket '{bucket_name}' not found. Creating it.")
                    self.client.make_bucket(bucket_name)
                    logger.info(f"Successfully created bucket '{bucket_name}'")
                else:
                    logger.debug(f"Bucket '{bucket_name}' already exists")
                    
            except S3Error as e:
                error_msg = f"S3 error while ensuring bucket '{bucket_name}' exists: {e}"
                logger.error(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error while ensuring bucket '{bucket_name}' exists: {e}"
                logger.error(error_msg)
                raise Exception(error_msg)

    def save_file(self, bucket_name: str, file_name: str, data: bytes):
        """
        Save file data to MinIO bucket
        Args:
            bucket_name: Target bucket name
            file_name: Object name/key in the bucket
            data: File data as bytes
        Raises:
            Exception: If save operation fails
        """
        logger.info(f"Saving file '{file_name}' to bucket '{bucket_name}' ({len(data)} bytes)")
        
        try:
            if not bucket_name or not file_name:
                raise ValueError("Bucket name and file name are required")
            
            if not data:
                raise ValueError("File data cannot be empty")
            
            # Save file to MinIO
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=file_name,
                data=BytesIO(data),
                length=len(data),
                content_type='application/octet-stream'
            )
            logger.info(f"Successfully saved file '{file_name}' to bucket '{bucket_name}'")
            
        except S3Error as e:
            error_msg = f"S3 error saving file '{file_name}' to bucket '{bucket_name}': {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error saving file '{file_name}' to bucket '{bucket_name}': {e}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def get_file(self, bucket_name: str, file_name: str) -> bytes:
        """
        Retrieve file data from MinIO bucket
        
        Args:
            bucket_name: Source bucket name
            file_name: Object name/key in the bucket
            
        Returns:
            File data as bytes
            
        Raises:
            Exception: If retrieval fails
        """
        logger.info(f"Retrieving file '{file_name}' from bucket '{bucket_name}'")
        response = None
        
        try:
            # Validate inputs
            if not bucket_name or not file_name:
                raise ValueError("Bucket name and file name are required")
            
            # Check if object exists
            try:
                self.client.stat_object(bucket_name, file_name)
            except S3Error as e:
                if e.code == 'NoSuchKey':
                    error_msg = f"File '{file_name}' not found in bucket '{bucket_name}'"
                    logger.warning(error_msg)
                    raise FileNotFoundError(error_msg)
                raise
            
            # Get file from MinIO
            response = self.client.get_object(bucket_name, file_name)
            data = response.read()
            
            logger.info(f"Successfully retrieved file '{file_name}' from bucket '{bucket_name}' ({len(data)} bytes)")
            return data
            
        except FileNotFoundError:
            raise
        except S3Error as e:
            error_msg = f"S3 error retrieving file '{file_name}' from bucket '{bucket_name}': {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error retrieving file '{file_name}' from bucket '{bucket_name}': {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
        finally:
            if response:
                response.close()
                response.release_conn()

# Singleton instance of MinioClient
try:
    minio_client = MinioClient()
except Exception as e:
    logger.error(f"Failed to create MinIO client singleton: {e}")
    raise