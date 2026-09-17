import aio_pika
from aio_pika.abc import AbstractRobustConnection

from user_management_service.config import settings

_connection: AbstractRobustConnection | None = None


async def get_rabbitmq_connection() -> AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    return _connection


async def close_rabbitmq_connection() -> None:
    global _connection
    if _connection is not None and not _connection.is_closed:
        await _connection.close()
    _connection = None
