from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from user_management_service.infrastructure.storage.s3 import S3ObjectStorage

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_s3_upload_puts_object_and_returns_path():
    storage = S3ObjectStorage(bucket="avatars", region="us-east-1")
    mock_client = AsyncMock()
    mock_client.put_object = AsyncMock()

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with patch.object(storage._session, "client", return_value=mock_cm) as client_factory:
        path = await storage.upload("users/1.png", b"image-bytes", "image/png")

    client_factory.assert_called_once()
    mock_client.put_object.assert_awaited_once_with(
        Bucket="avatars",
        Key="users/1.png",
        Body=b"image-bytes",
        ContentType="image/png",
    )
    assert path == "s3://avatars/users/1.png"
