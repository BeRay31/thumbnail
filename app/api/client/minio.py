import logging
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from app.core.config import settings

logger = logging.getLogger(__name__)

class MinioClient:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        self.init_buckets()

    def init_buckets(self):
        try:
            # Check and create the originals bucket
            if not self.client.bucket_exists(settings.MINIO_ORIGINALS_BUCKET):
                logger.info(f"Bucket '{settings.MINIO_ORIGINALS_BUCKET}' not found. Creating it.")
                self.client.make_bucket(settings.MINIO_ORIGINALS_BUCKET)
            
            # Check and create the thumbnails bucket
            if not self.client.bucket_exists(settings.MINIO_THUMBNAILS_BUCKET):
                logger.info(f"Bucket '{settings.MINIO_THUMBNAILS_BUCKET}' not found. Creating it.")
                self.client.make_bucket(settings.MINIO_THUMBNAILS_BUCKET)

        except S3Error as e:
            logger.error(f"Failed to ensure buckets exist due to minio client error: {e}")
            raise

    def save_file(self, bucket_name: str, file_name: str, data: bytes):
        logger.info(f"Saving file '{file_name}' to bucket '{bucket_name}'.")
        self.client.put_object(
            bucket_name=bucket_name,
            object_name=file_name,
            data=BytesIO(data),
            length=len(data),
            content_type='application/octet-stream'
        )

    def get_file(self, bucket_name: str, file_name: str) -> bytes:
        logger.info(f"Retrieving file '{file_name}' from bucket '{bucket_name}'.")
        response = None
        try:
            response = self.client.get_object(bucket_name, file_name)
            return response.read()
        except S3Error as e:
            logger.error(f"Failed to get file '{file_name}' from '{bucket_name}': {e}")
            raise
        finally:
            if response:
                response.close()
                response.release_conn()

# Singleton instance of StorageClient
minio_client = MinioClient()