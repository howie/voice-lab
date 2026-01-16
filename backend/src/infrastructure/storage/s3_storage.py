"""AWS S3 Storage Service Implementation."""

import aioboto3

from src.application.interfaces.storage_service import IStorageService, StoredFile


class S3StorageService(IStorageService):
    """AWS S3 storage implementation."""

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        endpoint_url: str | None = None,
    ):
        """Initialize S3 storage service.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            access_key_id: AWS access key (optional, uses default credentials if not provided)
            secret_access_key: AWS secret key (optional)
            endpoint_url: Custom endpoint URL (for S3-compatible services like MinIO)
        """
        self._bucket_name = bucket_name
        self._region = region
        self._access_key_id = access_key_id
        self._secret_access_key = secret_access_key
        self._endpoint_url = endpoint_url

        self._session = aioboto3.Session()

    def _get_client_config(self) -> dict:
        """Get boto3 client configuration."""
        config = {
            "region_name": self._region,
        }

        if self._access_key_id and self._secret_access_key:
            config["aws_access_key_id"] = self._access_key_id
            config["aws_secret_access_key"] = self._secret_access_key

        if self._endpoint_url:
            config["endpoint_url"] = self._endpoint_url

        return config

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StoredFile:
        """Upload data to S3."""
        config = self._get_client_config()

        async with self._session.client("s3", **config) as s3:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            await s3.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=data,
                **extra_args,
            )

        # Generate URL
        url = await self.get_url(key) or ""

        return StoredFile(
            key=key,
            url=url,
            size_bytes=len(data),
            content_type=content_type or "application/octet-stream",
        )

    async def download(self, key: str) -> bytes | None:
        """Download data from S3."""
        config = self._get_client_config()

        try:
            async with self._session.client("s3", **config) as s3:
                response = await s3.get_object(
                    Bucket=self._bucket_name,
                    Key=key,
                )
                return await response["Body"].read()
        except Exception:
            return None

    async def delete(self, key: str) -> bool:
        """Delete data from S3."""
        config = self._get_client_config()

        try:
            async with self._session.client("s3", **config) as s3:
                await s3.delete_object(
                    Bucket=self._bucket_name,
                    Key=key,
                )
                return True
        except Exception:
            return False

    async def get_url(self, key: str, expires_in: int = 3600) -> str | None:
        """Get presigned URL for accessing the file."""
        config = self._get_client_config()

        try:
            async with self._session.client("s3", **config) as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self._bucket_name,
                        "Key": key,
                    },
                    ExpiresIn=expires_in,
                )
                return url
        except Exception:
            return None

    async def exists(self, key: str) -> bool:
        """Check if file exists in S3."""
        config = self._get_client_config()

        try:
            async with self._session.client("s3", **config) as s3:
                await s3.head_object(
                    Bucket=self._bucket_name,
                    Key=key,
                )
                return True
        except Exception:
            return False
