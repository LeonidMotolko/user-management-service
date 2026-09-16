from redis.asyncio import Redis


class RedisTokenBlacklist:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def add(self, token_jti: str, ttl_seconds: int) -> None:
        await self.redis.setex(f"blacklist:{token_jti}", ttl_seconds, "true")

    async def is_blacklisted(self, token_jti: str) -> bool:
        return bool(await self.redis.exists(f"blacklist:{token_jti}"))
