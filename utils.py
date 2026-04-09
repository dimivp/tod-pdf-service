"""Utility functions for MinIO, logging, and file handling."""

import logging
import os
from io import BytesIO
from typing import Optional
from datetime import timedelta
import uuid

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MinIOClient:
    """Wrapper for MinIO S3 client operations."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = True,
    ):
        """Initialize MinIO client."""
        self.endpoint = endpoint
        self.bucket = bucket
        self.secure = secure

        try:
            self.client = boto3.client(
                "s3",
                endpoint_url=f"{'https' if secure else 'http'}://{endpoint}",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                verify=secure,
            )
            logger.info(f"MinIO client initialized: {endpoint}/{bucket}")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            self.client = None

    def upload_file(
        self,
        file_bytes: bytes,
        object_name: str,
        content_type: str = "application/pdf",
    ) -> bool:
        """Upload file bytes to MinIO.

        Args:
            file_bytes: File content as bytes
            object_name: Path in MinIO (e.g., "pdfs/TOD_1-234-5_2026-04-09_Antwerpen.pdf")
            content_type: MIME type

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.warning("MinIO client not available, skipping upload")
            return False

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_name,
                Body=BytesIO(file_bytes),
                ContentType=content_type,
            )
            logger.info(f"Uploaded {object_name} to MinIO")
            return True
        except ClientError as e:
            logger.error(f"MinIO upload failed: {e}")
            return False

    def get_signed_url(
        self, object_name: str, expiration_hours: int = 1
    ) -> Optional[str]:
        """Generate signed URL for file access.

        Args:
            object_name: Path in MinIO
            expiration_hours: URL expiration in hours

        Returns:
            Signed URL or None if failed
        """
        if not self.client:
            logger.warning("MinIO client not available, cannot generate signed URL")
            return None

        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_name},
                ExpiresIn=int(timedelta(hours=expiration_hours).total_seconds()),
            )
            logger.debug(f"Generated signed URL for {object_name}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return None


def get_minio_client() -> Optional[MinIOClient]:
    """Get MinIO client from environment variables.

    Returns:
        MinIOClient instance or None if env vars not configured
    """
    endpoint = os.getenv("MINIO_ENDPOINT")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    bucket = os.getenv("MINIO_BUCKET", "logboek-pdfs")

    if not all([endpoint, access_key, secret_key]):
        logger.debug("MinIO not configured (missing env vars)")
        return None

    return MinIOClient(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
        secure=True,
    )


def generate_request_id() -> str:
    """Generate unique request ID for logging."""
    return str(uuid.uuid4())[:8]


def log_request(request_id: str, method: str, path: str, **kwargs):
    """Log HTTP request."""
    logger.info(f"[{request_id}] {method} {path} | {kwargs}")


def log_error(request_id: str, error: Exception, **kwargs):
    """Log error with request ID."""
    logger.error(f"[{request_id}] Error: {type(error).__name__}: {str(error)} | {kwargs}")
