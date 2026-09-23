from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from user_management_service.application.interfaces.user_repository import (
    IUserRepository,
)
from user_management_service.domain.entities.user import User
from user_management_service.infrastructure.database.models import UserModel


class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user: User) -> User:
        user_model = UserModel(
            id=user.id,
            name=user.name,
            surname=user.surname,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            phone_number=user.phone_number,
            image_s3_path=user.image_s3_path,
            is_blocked=user.is_blocked,
        )
        self.session.add(user_model)
        await self.session.commit()
        await self.session.refresh(user_model)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return User(
            id=model.id,
            name=model.name,
            surname=model.surname,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            role=model.role,
            phone_number=model.phone_number,
            image_s3_path=model.image_s3_path,
            is_blocked=model.is_blocked,
            created_at=model.created_at,
            modified_at=model.modified_at,
        )

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return User(
            id=model.id,
            name=model.name,
            surname=model.surname,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            role=model.role,
            phone_number=model.phone_number,
            image_s3_path=model.image_s3_path,
            is_blocked=model.is_blocked,
            created_at=model.created_at,
            modified_at=model.modified_at,
        )

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return User(
            id=model.id,
            name=model.name,
            surname=model.surname,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            role=model.role,
            phone_number=model.phone_number,
            image_s3_path=model.image_s3_path,
            is_blocked=model.is_blocked,
            created_at=model.created_at,
            modified_at=model.modified_at,
        )

    async def update(self, user: User) -> User:
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"User with id {user.id} not found in DB")

        model.name = user.name
        model.surname = user.surname
        model.phone_number = user.phone_number
        model.is_blocked = user.is_blocked
        model.image_s3_path = user.image_s3_path

        await self.session.commit()
        await self.session.refresh(model)
        return user

    async def delete(self, user_id: UUID) -> bool:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self.session.delete(model)
        await self.session.commit()
        return True
