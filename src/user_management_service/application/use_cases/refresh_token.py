from uuid import UUID, uuid4

import jwt

from user_management_service.application.dto.auth import RefreshTokenDTO, TokenResponseDTO
from user_management_service.application.interfaces.user_repository import IUserRepository
from user_management_service.domain.exceptions import DomainError, UserNotFoundError
from user_management_service.infrastructure.security.jwt_service import JWTService
from user_management_service.infrastructure.security.token_blacklist import RedisTokenBlacklist


class InvalidTokenError(DomainError):
    def __init__(self, message: str = "Invalid or expired refresh token."):
        super().__init__(message)


class RefreshTokenUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        jwt_service: JWTService,
        blacklist: RedisTokenBlacklist,
    ):
        self.user_repo = user_repo
        self.jwt_service = jwt_service
        self.blacklist = blacklist

    async def execute(self, dto: RefreshTokenDTO) -> TokenResponseDTO:
        try:
            payload = self.jwt_service.decode_token(dto.refresh_token)
        except jwt.PyJWTError as e:
            raise InvalidTokenError("Token decoding failed.") from e

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Not a refresh token.")

        jti = payload.get("jti")
        if not jti or await self.blacklist.is_blacklisted(jti):
            raise InvalidTokenError("Token is blacklisted.")

        user_id = UUID(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        exp = payload.get("exp", 0)
        import time

        ttl = int(exp - time.time())
        if ttl > 0:
            await self.blacklist.add(jti, ttl)

        new_jti = str(uuid4())
        access_token = self.jwt_service.create_access_token(user.id, user.role.value)
        new_refresh_token = self.jwt_service.create_refresh_token(user.id, new_jti)

        return TokenResponseDTO(access_token=access_token, refresh_token=new_refresh_token)
