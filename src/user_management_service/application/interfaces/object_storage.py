from abc import ABC, abstractmethod


class IObjectStorage(ABC):
    @abstractmethod
    async def upload(self, key: str, body: bytes, content_type: str) -> str:
        """Upload an object and return its storage key / S3 path."""
