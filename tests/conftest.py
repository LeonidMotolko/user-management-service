from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from user_management_service.config import settings
from user_management_service.domain.entities.role import Role
from user_management_service.infrastructure.database.models import (
    Base,
    GroupModel,
    UserModel,
)
from user_management_service.infrastructure.database.session import (
    get_async_session,
)
from user_management_service.infrastructure.security.jwt_service import JWTService
from user_management_service.infrastructure.security.password_hasher import (
    PBKDF2PasswordHasher,
)
from user_management_service.main import app

TEST_DB_NAME = "user_db_test"

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER.get_secret_value()}"
    f":{settings.POSTGRES_PASSWORD.get_secret_value()}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{TEST_DB_NAME}"
)
ADMIN_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER.get_secret_value()}"
    f":{settings.POSTGRES_PASSWORD.get_secret_value()}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/postgres"
)


@pytest_asyncio.fixture(scope="session")
async def _test_engine():
    admin_engine = create_async_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        from sqlalchemy import text

        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_NAME},
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    await admin_engine.dispose()

    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_test_engine) -> AsyncGenerator[AsyncSession]:
    connection = await _test_engine.connect()
    outer_transaction = await connection.begin()

    session_maker = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = session_maker()

    try:
        yield session
    finally:
        await session.close()
        await outer_transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:

    async def _override_get_async_session():
        yield db_session

    app.dependency_overrides[get_async_session] = _override_get_async_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def password_hasher() -> PBKDF2PasswordHasher:
    return PBKDF2PasswordHasher()


@pytest.fixture(scope="session")
def jwt_service() -> JWTService:
    return JWTService(
        secret_key=settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
        access_ttl_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_ttl_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


@pytest_asyncio.fixture
async def make_group(db_session: AsyncSession) -> Callable:

    async def _make_group(name: str = "Test Group") -> GroupModel:
        group = GroupModel(name=name, created_at=datetime.now(UTC))
        db_session.add(group)
        await db_session.flush()
        await db_session.refresh(group)
        return group

    return _make_group


@pytest_asyncio.fixture
async def make_user(db_session: AsyncSession, password_hasher: PBKDF2PasswordHasher) -> Callable:

    async def _make_user(
        role: Role = Role.USER,
        group_id: int | None = None,
        password: str = "Password123!",
        **overrides,
    ) -> tuple[UserModel, str]:
        unique = uuid4().hex[:8]
        defaults = {
            "id": uuid4(),
            "name": "Test",
            "surname": "User",
            "username": f"user_{unique}",
            "email": f"user_{unique}@example.com",
            "password_hash": password_hasher.hash(password),
            "role": role,
            "group_id": group_id,
            "is_blocked": False,
        }
        defaults.update(overrides)
        user = UserModel(**defaults)
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)
        return user, password

    return _make_user


def auth_headers(jwt_service: JWTService, user_id: UUID, role: str) -> dict[str, str]:
    token = jwt_service.create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}
