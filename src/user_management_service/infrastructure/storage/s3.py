import aioboto3

from user_management_service.application.interfaces.object_storage import IObjectStorage


class S3ObjectStorage(IObjectStorage):
    def __init__(
        self,
        bucket: str,
        region: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url or None
        self.access_key_id = access_key_id or None
        self.secret_access_key = secret_access_key or None
        self._session = aioboto3.Session()

    async def upload(self, key: str, body: bytes, content_type: str) -> str:
        client_kwargs: dict[str, str] = {"region_name": self.region}
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url
        if self.access_key_id and self.secret_access_key:
            client_kwargs["aws_access_key_id"] = self.access_key_id
            client_kwargs["aws_secret_access_key"] = self.secret_access_key

        async with self._session.client("s3", **client_kwargs) as client:
            await client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=body,
                ContentType=content_type,
            )
        return f"s3://{self.bucket}/{key}"
