from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ResetPasswordMessage:
    email: str
    subject: str
    body: str
    published_at: datetime


class IMessagePublisher(ABC):
    @abstractmethod
    async def publish_reset_password(self, message: ResetPasswordMessage) -> None:
        """Publish a reset-password email message to the message broker."""
