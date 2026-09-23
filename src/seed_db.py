import asyncio
import random
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from user_management_service.config import settings
from user_management_service.infrastructure.database.models import (
    GroupModel,
    RoleEnum,
    UserModel,
)
from user_management_service.infrastructure.security.password_hasher import (
    PBKDF2PasswordHasher,
)

DEMO_PASSWORD = "DemoPass123!"

GROUP_NAMES = ["Support", "Sales", "Engineering", "QA", "Marketing"]

FIRST_NAMES = [
    "Anna",
    "Ivan",
    "Olga",
    "Petr",
    "Maria",
    "Sergey",
    "Elena",
    "Dmitry",
    "Natalia",
    "Alexey",
    "Ekaterina",
    "Mikhail",
    "Tatiana",
    "Andrey",
    "Yulia",
    "Nikolay",
    "Svetlana",
    "Pavel",
    "Irina",
    "Vladimir",
]
LAST_NAMES = [
    "Kuznetsova",
    "Ivanov",
    "Smirnova",
    "Petrov",
    "Volkova",
    "Sokolov",
    "Popova",
    "Fedorov",
    "Morozova",
    "Volkov",
]

hasher = PBKDF2PasswordHasher()


async def get_or_create_group(session, name: str) -> GroupModel:
    result = await session.execute(select(GroupModel).where(GroupModel.name == name))
    group = result.scalar_one_or_none()
    if group:
        return group
    group = GroupModel(name=name, created_at=datetime.now(UTC))
    session.add(group)
    await session.flush()
    return group


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        # 1. группы (get-or-create, чтобы не плодить дубли при повторном запуске)
        groups = [await get_or_create_group(session, name) for name in GROUP_NAMES]
        await session.commit()

        # 2. чистим предыдущих demo-юзеров, если скрипт уже запускался
        existing = await session.execute(select(UserModel).where(UserModel.username.like("demo_%")))
        for u in existing.scalars().all():
            await session.delete(u)
        await session.commit()

        password_hash = hasher.hash(DEMO_PASSWORD)
        created: list[UserModel] = []

        # 3. администраторы — без группы, видят всех
        for i in range(1, 4):
            created.append(
                UserModel(
                    name=random.choice(FIRST_NAMES),
                    surname=random.choice(LAST_NAMES),
                    username=f"demo_admin_{i}",
                    email=f"demo_admin_{i}@example.com",
                    password_hash=password_hash,
                    phone_number=f"+7900000{i:04d}",
                    role=RoleEnum.ADMIN,
                    group_id=None,
                )
            )

        # 4. по одному модератору на каждую группу
        for i, group in enumerate(groups, start=1):
            created.append(
                UserModel(
                    name=random.choice(FIRST_NAMES),
                    surname=random.choice(LAST_NAMES),
                    username=f"demo_mod_{i}",
                    email=f"demo_mod_{i}@example.com",
                    password_hash=password_hash,
                    phone_number=f"+7900001{i:04d}",
                    role=RoleEnum.MODERATOR,
                    group_id=group.id,
                )
            )

        # 5. остальные — обычные пользователи, разбросаны по группам
        #    (плюс None, None в списке выбора — часть юзеров без группы вообще)
        remaining = 50 - len(created)
        pool = groups + [None, None]
        for i in range(1, remaining + 1):
            group = random.choice(pool)
            created.append(
                UserModel(
                    name=random.choice(FIRST_NAMES),
                    surname=random.choice(LAST_NAMES),
                    username=f"demo_user_{i:03d}",
                    email=f"demo_user_{i:03d}@example.com",
                    password_hash=password_hash,
                    phone_number=f"+7900002{i:04d}",
                    role=RoleEnum.USER,
                    group_id=group.id if group else None,
                    is_blocked=(i % 17 == 0),  # пара заблокированных — показать 403 на демо
                )
            )

        session.add_all(created)
        await session.commit()

        print(f"Групп создано/найдено: {len(groups)}")
        print(f"Пользователей создано: {len(created)}")
        print("  - ADMIN: 3 (demo_admin_1..3)")
        print(f"  - MODERATOR: {len(groups)} (demo_mod_1..{len(groups)}, по одному на группу)")
        print(f"  - USER: {remaining} (demo_user_001..{remaining:03d})")
        print(f"Единый пароль для всех demo_* пользователей: {DEMO_PASSWORD}")
        print(
            "Заблокированы (is_blocked=true): "
            + ", ".join(f"demo_user_{i:03d}" for i in range(1, remaining + 1) if i % 17 == 0)
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
