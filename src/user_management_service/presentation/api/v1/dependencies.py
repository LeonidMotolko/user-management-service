from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from user_management_service.application.interfaces.password_hasher import (
    IPasswordHasher,
)
from user_management_service.application.interfaces.user_repository import (
    IUserRepository,
)
from user_management_service.application.use_cases.create_user import (
    CreateUserUseCase,
)
from user_management_service.application.use_cases.delete_user import (
    DeleteUserUseCase,
)
from user_management_service.application.use_cases.get_user import (
    GetUserUseCase,
)
from user_management_service.application.use_cases.list_users import (
    ListUsersUseCase,
)
from user_management_service.application.use_cases.login_user import (
    LoginUserUseCase,
)
from user_management_service.application.use_cases.refresh_token import (
    RefreshTokenUseCase,
)
from user_management_service.application.use_cases.update_user import (
    UpdateUserUseCase,
)
from user_management_service.config import settings
from user_management_service.domain.entities.role import Role
from user_management_service.domain.entities.user import User
from user_management_service.infrastructure.database.session import (
    get_async_session,
)
from user_management_service.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from user_management_service.infrastructure.security.jwt_service import (
    JWTService,
)
from user_management_service.infrastructure.security.password_hasher import (
    PBKDF2PasswordHasher,
)
from user_management_service.infrastructure.security.token_blacklist import (
    RedisTokenBlacklist,
)

security = HTTPBearer()

# --- Infrastructure Dependencies ---


async def get_redis_client() -> AsyncGenerator[Redis]:
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


def get_jwt_service() -> JWTService:
    return JWTService(
        secret_key=settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
        access_ttl_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_ttl_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_token_blacklist(
    redis_client: Annotated[Redis, Depends(get_redis_client)],
) -> RedisTokenBlacklist:
    return RedisTokenBlacklist(redis_client)


def get_password_hasher() -> IPasswordHasher:
    return PBKDF2PasswordHasher()


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> IUserRepository:
    return SQLAlchemyUserRepository(session)


# --- Application Use Cases Dependencies ---


def get_create_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
) -> CreateUserUseCase:
    return CreateUserUseCase(
        user_repository=user_repo,
        password_hasher=password_hasher,
    )


def get_login_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> LoginUserUseCase:
    return LoginUserUseCase(
        user_repo=user_repo,
        password_hasher=password_hasher,
        jwt_service=jwt_service,
    )


def get_refresh_token_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    blacklist: Annotated[RedisTokenBlacklist, Depends(get_token_blacklist)],
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(
        user_repo=user_repo,
        jwt_service=jwt_service,
        blacklist=blacklist,
    )


def get_get_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> GetUserUseCase:
    return GetUserUseCase(user_repo=user_repo)


def get_update_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> UpdateUserUseCase:
    return UpdateUserUseCase(user_repo=user_repo)


def get_delete_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> DeleteUserUseCase:
    return DeleteUserUseCase(user_repo=user_repo)


def get_list_users_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> ListUsersUseCase:
    return ListUsersUseCase(user_repo=user_repo)


# --- Auth Guard ---


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> User:
    token = credentials.credentials
    try:
        payload = jwt_service.decode_token(token)
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = UUID(payload["sub"])
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked",
        )

    return user


def require_roles(*allowed_roles: Role):
    """Dependency factory: пускает только пользователей с одной из ролей."""

    async def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


async def require_admin_or_same_group(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> User:
    """Guard для GET /user/<user_id>: ADMIN видит всех,
    MODERATOR — только пользователей из своей группы."""
    if current_user.role == Role.ADMIN:
        return current_user

    if current_user.role == Role.MODERATOR:
        if not current_user.group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Moderator is not assigned to a group",
            )
        target_user = await user_repo.get_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if target_user.group and target_user.group.id == current_user.group.id:
            return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions",
    )
