from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt


class JWTService:
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_ttl_minutes: int = 15,
        refresh_ttl_days: int = 7,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_ttl = timedelta(minutes=access_ttl_minutes)
        self.refresh_ttl = timedelta(days=refresh_ttl_days)

    def create_access_token(self, user_id: UUID, role: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "role": role,
            "type": "access",
            "iat": now,
            "exp": now + self.access_ttl,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: UUID, jti: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "jti": jti,
            "type": "refresh",
            "iat": now,
            "exp": now + self.refresh_ttl,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
