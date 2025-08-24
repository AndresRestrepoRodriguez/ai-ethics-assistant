import logging

import aioboto3

from ai_ethics_assistant.configuration import S3Config

logger = logging.getLogger(__name__)


class S3ServiceError(Exception):
    pass


class S3Service:
    def __init__(self, config: S3Config):
        self.config = config
        self._session = aioboto3.Session(
            aws_access_key_id=config.access_key_id.get_secret_value(),
            aws_secret_access_key=config.secret_access_key.get_secret_value(),
            region_name=config.region,
        )

    async def list_pdfs(self, prefix: str = "") -> list[str]:
        """List all PDF files in the bucket with the given prefix"""
        try:
            full_prefix = (
                self.config.pdf_prefix + prefix if prefix else self.config.pdf_prefix
            )

            async with self._session.client("s3") as s3:
                paginator = s3.get_paginator("list_objects_v2")
                pdf_keys = []

                async for page in paginator.paginate(
                    Bucket=self.config.bucket_name, Prefix=full_prefix
                ):
                    if "Contents" in page:
                        for obj in page["Contents"]:
                            key = obj.get("Key", "")
                            if key and key.lower().endswith(".pdf"):
                                pdf_keys.append(key)

                logger.info(
                    f"Found {len(pdf_keys)} PDF files in bucket {self.config.bucket_name}"
                )
                return pdf_keys

        except Exception as e:
            raise S3ServiceError(f"Failed to list PDFs: {e}")

    async def download_pdf(self, key: str) -> bytes:
        """Download a PDF file by key and return its content as bytes"""
        try:
            async with self._session.client("s3") as s3:
                response = await s3.get_object(Bucket=self.config.bucket_name, Key=key)
                content = await response["Body"].read()

                logger.info(f"Downloaded PDF {key} ({len(content)} bytes)")
                return content

        except Exception as e:
            raise S3ServiceError(f"Failed to download PDF '{key}': {e}")

    async def test_connection(self) -> bool:
        """Test S3 bucket access by attempting to list objects"""
        try:
            async with self._session.client("s3") as s3:
                await s3.list_objects_v2(
                    Bucket=self.config.bucket_name,
                    Prefix=self.config.pdf_prefix,
                    MaxKeys=1,
                )

                logger.info(
                    f"Successfully connected to S3 bucket '{self.config.bucket_name}'"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to connect to S3: {e}")
            return False
