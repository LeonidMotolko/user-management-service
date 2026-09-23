from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from user_management_service.application.dto.auth import LoginDTO, RefreshTokenDTO
from user_management_service.application.dto.user import CreateUserDTO, UpdateUserDTO
from user_management_service.application.use_cases.create_user import CreateUserUseCase
from user_management_service.application.use_cases.delete_user import DeleteUserUseCase
from user_management_service.application.use_cases.get_user import GetUserUseCase
from user_management_service.application.use_cases.list_users import ListUsersUseCase
from user_management_service.application.use_cases.login_user import (
    InvalidCredentialsError,
    LoginUserUseCase,
)
from user_management_service.application.use_cases.refresh_token import (
    InvalidTokenError,
    RefreshTokenUseCase,
)
from user_management_service.application.use_cases.update_user import UpdateUserUseCase
from user_management_service.domain.entities.role import Role
from user_management_service.domain.entities.user import User
from user_management_service.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


def make_domain_user(**overrides) -> User:
    defaults = dict(
        id=uuid4(),
        name="Test",
        surname="User",
        username="testuser",
        email="test@example.com",
        password_hash="hashed:password",
        role=Role.USER,
        phone_number=None,
        group=None,
        image_s3_path=None,
        is_blocked=False,
        created_at=datetime.now(UTC),
        modified_at=datetime.now(UTC),
    )
    defaults.update(overrides)
    return User(**defaults)


class TestCreateUserUseCase:
    async def test_creates_user_when_email_and_username_free(self):
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = None
        user_repo.get_by_username.return_value = None
        user_repo.add.side_effect = lambda user: user

        password_hasher = MagicMock()
        password_hasher.hash.return_value = "hashed:StrongPass123"

        use_case = CreateUserUseCase(user_repository=user_repo, password_hasher=password_hasher)
        dto = CreateUserDTO(
            name="Alice",
            surname="Smith",
            username="alice",
            email="alice@example.com",
            password="StrongPass123",
        )

        result = await use_case.execute(dto)

        assert result.email == "alice@example.com"
        assert result.role == Role.USER
        password_hasher.hash.assert_called_once_with("StrongPass123")
        user_repo.add.assert_awaited_once()

    async def test_raises_when_email_taken(self):
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = make_domain_user(email="taken@example.com")

        use_case = CreateUserUseCase(user_repository=user_repo, password_hasher=MagicMock())
        dto = CreateUserDTO(
            name="Bob",
            surname="Jones",
            username="bob",
            email="taken@example.com",
            password="StrongPass123",
        )

        with pytest.raises(UserAlreadyExistsError):
            await use_case.execute(dto)

        user_repo.add.assert_not_called()

    async def test_raises_when_username_taken(self):
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = None
        user_repo.get_by_username.return_value = make_domain_user(username="taken")

        use_case = CreateUserUseCase(user_repository=user_repo, password_hasher=MagicMock())
        dto = CreateUserDTO(
            name="Carl",
            surname="Doe",
            username="taken",
            email="carl@example.com",
            password="StrongPass123",
        )

        with pytest.raises(UserAlreadyExistsError):
            await use_case.execute(dto)


class TestLoginUserUseCase:
    async def test_login_succeeds_with_correct_password(self):
        user = make_domain_user(email="alice@example.com", password_hash="hashed:pw")
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = user

        password_hasher = MagicMock()
        password_hasher.verify.return_value = True

        jwt_service = MagicMock()
        jwt_service.create_access_token.return_value = "access-token"
        jwt_service.create_refresh_token.return_value = "refresh-token"

        use_case = LoginUserUseCase(user_repo=user_repo, password_hasher=password_hasher, jwt_service=jwt_service)

        result = await use_case.execute(LoginDTO(login="alice@example.com", password="pw"))

        assert result.access_token == "access-token"
        assert result.refresh_token == "refresh-token"

    async def test_login_fails_with_wrong_password(self):
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = make_domain_user()

        password_hasher = MagicMock()
        password_hasher.verify.return_value = False

        use_case = LoginUserUseCase(user_repo=user_repo, password_hasher=password_hasher, jwt_service=MagicMock())

        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(LoginDTO(login="test@example.com", password="wrong"))

    async def test_login_fails_when_user_not_found(self):
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = None
        user_repo.get_by_username.return_value = None
        user_repo.get_by_phone_number.return_value = None

        use_case = LoginUserUseCase(user_repo=user_repo, password_hasher=MagicMock(), jwt_service=MagicMock())

        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(LoginDTO(login="ghost", password="whatever"))

    async def test_login_by_phone_number_is_supported(self):
        user = make_domain_user(phone_number="+79990000000")
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = None
        user_repo.get_by_username.return_value = None
        user_repo.get_by_phone_number.return_value = user

        password_hasher = MagicMock()
        password_hasher.verify.return_value = True

        jwt_service = MagicMock()
        jwt_service.create_access_token.return_value = "access-token"
        jwt_service.create_refresh_token.return_value = "refresh-token"

        use_case = LoginUserUseCase(user_repo=user_repo, password_hasher=password_hasher, jwt_service=jwt_service)

        result = await use_case.execute(LoginDTO(login="+79990000000", password="pw"))
        assert result.access_token == "access-token"

    async def test_login_fails_when_user_is_blocked(self):
        user = make_domain_user(is_blocked=True)
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = user

        password_hasher = MagicMock()
        password_hasher.verify.return_value = True

        use_case = LoginUserUseCase(user_repo=user_repo, password_hasher=password_hasher, jwt_service=MagicMock())

        with pytest.raises(InvalidCredentialsError):
            await use_case.execute(LoginDTO(login="test@example.com", password="pw"))


class TestRefreshTokenUseCase:
    async def test_refresh_succeeds_and_blacklists_old_token(self):
        user = make_domain_user()
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = user

        jwt_service = MagicMock()
        jwt_service.decode_token.return_value = {
            "type": "refresh",
            "jti": "old-jti",
            "sub": str(user.id),
            "exp": 9999999999,
        }
        jwt_service.create_access_token.return_value = "new-access"
        jwt_service.create_refresh_token.return_value = "new-refresh"

        blacklist = AsyncMock()
        blacklist.is_blacklisted.return_value = False

        use_case = RefreshTokenUseCase(user_repo=user_repo, jwt_service=jwt_service, blacklist=blacklist)

        result = await use_case.execute(
            RefreshTokenDTO(refresh_token="some-token"),
            current_user_id=user.id,
        )

        assert result.access_token == "new-access"
        blacklist.add.assert_awaited_once()
        assert blacklist.add.call_args.args[0] == "old-jti"

    async def test_refresh_fails_when_token_type_is_not_refresh(self):
        jwt_service = MagicMock()
        jwt_service.decode_token.return_value = {"type": "access"}

        use_case = RefreshTokenUseCase(user_repo=AsyncMock(), jwt_service=jwt_service, blacklist=AsyncMock())

        with pytest.raises(InvalidTokenError):
            await use_case.execute(
                RefreshTokenDTO(refresh_token="access-token-not-refresh"),
                current_user_id=uuid4(),
            )

    async def test_refresh_fails_when_token_is_blacklisted(self):
        jwt_service = MagicMock()
        jwt_service.decode_token.return_value = {
            "type": "refresh",
            "jti": "blacklisted-jti",
        }
        blacklist = AsyncMock()
        blacklist.is_blacklisted.return_value = True

        use_case = RefreshTokenUseCase(user_repo=AsyncMock(), jwt_service=jwt_service, blacklist=blacklist)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(
                RefreshTokenDTO(refresh_token="blacklisted"),
                current_user_id=uuid4(),
            )

    async def test_refresh_fails_when_user_no_longer_exists(self):
        user_id = uuid4()
        jwt_service = MagicMock()
        jwt_service.decode_token.return_value = {
            "type": "refresh",
            "jti": "jti",
            "sub": str(user_id),
        }
        blacklist = AsyncMock()
        blacklist.is_blacklisted.return_value = False

        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = None

        use_case = RefreshTokenUseCase(user_repo=user_repo, jwt_service=jwt_service, blacklist=blacklist)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(
                RefreshTokenDTO(refresh_token="orphaned"),
                current_user_id=user_id,
            )

    async def test_refresh_fails_when_token_belongs_to_another_user(self):
        jwt_service = MagicMock()
        jwt_service.decode_token.return_value = {
            "type": "refresh",
            "jti": "jti",
            "sub": str(uuid4()),
        }
        blacklist = AsyncMock()
        blacklist.is_blacklisted.return_value = False

        use_case = RefreshTokenUseCase(
            user_repo=AsyncMock(),
            jwt_service=jwt_service,
            blacklist=blacklist,
        )

        with pytest.raises(InvalidTokenError):
            await use_case.execute(
                RefreshTokenDTO(refresh_token="stolen-refresh"),
                current_user_id=uuid4(),
            )


class TestGetUserUseCase:
    async def test_returns_user_when_found(self):
        user = make_domain_user()
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = user

        result = await GetUserUseCase(user_repo=user_repo).execute(user.id)
        assert result.id == user.id

    async def test_raises_when_not_found(self):
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await GetUserUseCase(user_repo=user_repo).execute(uuid4())


class TestUpdateUserUseCase:
    async def test_updates_only_provided_fields(self):
        user = make_domain_user(name="Old", surname="Name")
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = user
        user_repo.update.side_effect = lambda u: u

        use_case = UpdateUserUseCase(user_repo=user_repo)
        result = await use_case.execute(user.id, UpdateUserDTO(name="New"))

        assert result.name == "New"
        assert result.surname == "Name"

    async def test_raises_when_user_not_found(self):
        user_repo = AsyncMock()
        user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await UpdateUserUseCase(user_repo=user_repo).execute(uuid4(), UpdateUserDTO(name="X"))


class TestDeleteUserUseCase:
    async def test_deletes_existing_user(self):
        user_repo = AsyncMock()
        user_repo.delete.return_value = True

        await DeleteUserUseCase(user_repo=user_repo).execute(uuid4())
        user_repo.delete.assert_awaited_once()

    async def test_raises_when_user_not_found(self):
        user_repo = AsyncMock()
        user_repo.delete.return_value = False

        with pytest.raises(UserNotFoundError):
            await DeleteUserUseCase(user_repo=user_repo).execute(uuid4())


class TestListUsersUseCase:
    async def test_wraps_repository_result_into_paginated_dto(self):
        from user_management_service.application.interfaces.user_repository import (
            UserListFilter,
        )

        users = [make_domain_user(), make_domain_user()]
        user_repo = AsyncMock()
        user_repo.list_users.return_value = (users, 42)

        filters = UserListFilter(page=2, limit=10)
        result = await ListUsersUseCase(user_repo=user_repo).execute(filters)

        assert len(result.items) == 2
        assert result.total == 42
        assert result.page == 2
        assert result.limit == 10
        user_repo.list_users.assert_awaited_once_with(filters)
