from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from user_management_service.application.use_cases.block_user import (
    BlockUserUseCase,
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
from user_management_service.application.use_cases.update_user import (
    UpdateUserUseCase,
)
from user_management_service.infrastructure.database.session import (
    async_session_maker,
)
from user_management_service.infrastructure.repositories.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from user_management_service.infrastructure.security.password_hasher import (
    PBKDF2PasswordHasher,
)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session)


def get_password_hasher() -> PBKDF2PasswordHasher:
    return PBKDF2PasswordHasher()


def get_create_user_use_case(
    repo: Annotated[SQLAlchemyUserRepository, Depends(get_user_repository)],
    hasher: Annotated[PBKDF2PasswordHasher, Depends(get_password_hasher)],
) -> CreateUserUseCase:
    return CreateUserUseCase(user_repository=repo, password_hasher=hasher)


def get_get_user_use_case(
    repo: Annotated[SQLAlchemyUserRepository, Depends(get_user_repository)],
) -> GetUserUseCase:
    return GetUserUseCase(user_repo=repo)


def get_update_user_use_case(
    repo: Annotated[SQLAlchemyUserRepository, Depends(get_user_repository)],
) -> UpdateUserUseCase:
    return UpdateUserUseCase(user_repo=repo)


def get_delete_user_use_case(
    repo: Annotated[SQLAlchemyUserRepository, Depends(get_user_repository)],
) -> DeleteUserUseCase:
    return DeleteUserUseCase(user_repo=repo)


def get_block_user_use_case(
    repo: Annotated[SQLAlchemyUserRepository, Depends(get_user_repository)],
) -> BlockUserUseCase:
    return BlockUserUseCase(user_repo=repo)
