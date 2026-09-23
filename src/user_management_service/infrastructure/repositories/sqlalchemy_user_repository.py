from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from user_management_service.application.interfaces.user_repository import (
    IUserRepository,
    UserListFilter,
)
from user_management_service.domain.entities.group import Group
from user_management_service.domain.entities.user import User
from user_management_service.infrastructure.database.models import UserModel


class SQLAlchemyUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            name=model.name,
            surname=model.surname,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            role=model.role,
            phone_number=model.phone_number,
            group=Group(id=model.group.id, name=model.group.name, created_at=model.group.created_at)
            if model.group
            else None,
            image_s3_path=model.image_s3_path,
            is_blocked=model.is_blocked,
            created_at=model.created_at,
            modified_at=model.modified_at,
        )

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
            group_id=user.group.id if user.group else None,
            image_s3_path=user.image_s3_path,
            is_blocked=user.is_blocked,
        )
        self.session.add(user_model)
        await self.session.commit()
        await self.session.refresh(user_model, attribute_names=["group"])
        return self._to_entity(user_model)

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(UserModel).options(selectinload(UserModel.group)).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).options(selectinload(UserModel.group)).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).options(selectinload(UserModel.group)).where(UserModel.username == username)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, user: User) -> User:
        stmt = select(UserModel).options(selectinload(UserModel.group)).where(UserModel.id == user.id)
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
        await self.session.refresh(model, attribute_names=["group", "modified_at"])
        return self._to_entity(model)

    async def delete(self, user_id: UUID) -> bool:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self.session.delete(model)
        await self.session.commit()
        return True

    async def list_users(self, filters: UserListFilter) -> tuple[list[User], int]:
        conditions = []
        if filters.filter_by_name:
            pattern = f"%{filters.filter_by_name}%"
            conditions.append(or_(UserModel.name.ilike(pattern), UserModel.surname.ilike(pattern)))
        if filters.restrict_to_group:
            # MODERATOR: если у него самого нет группы — он не должен видеть никого
            conditions.append(UserModel.group_id == filters.group_id if filters.group_id is not None else False)

        sort_column = getattr(UserModel, filters.sort_by)
        order_clause = sort_column.asc() if filters.order_by == "asc" else sort_column.desc()

        base_stmt = select(UserModel)
        count_stmt = select(func.count()).select_from(UserModel)
        for condition in conditions:
            base_stmt = base_stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            base_stmt.options(selectinload(UserModel.group))
            .order_by(order_clause)
            .offset((filters.page - 1) * filters.limit)
            .limit(filters.limit)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models], total
