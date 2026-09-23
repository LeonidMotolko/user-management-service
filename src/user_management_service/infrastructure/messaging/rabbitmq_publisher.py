import json

from aio_pika import DeliveryMode, Message
from aio_pika.abc import AbstractRobustConnection

from user_management_service.application.interfaces.message_publisher import (
    IMessagePublisher,
    ResetPasswordMessage,
)

RESET_PASSWORD_QUEUE = "reset-password-stream"


class RabbitMQPublisher(IMessagePublisher):
    def __init__(self, connection: AbstractRobustConnection):
        self._connection = connection

    async def publish_reset_password(self, message: ResetPasswordMessage) -> None:
        channel = await self._connection.channel()
        try:
            await channel.declare_queue(RESET_PASSWORD_QUEUE, durable=True)
            payload = {
                "email": message.email,
                "subject": message.subject,
                "body": message.body,
                "published_at": message.published_at.isoformat(),
            }
            await channel.default_exchange.publish(
                Message(
                    body=json.dumps(payload).encode("utf-8"),
                    content_type="application/json",
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                routing_key=RESET_PASSWORD_QUEUE,
            )
        finally:
            await channel.close()
