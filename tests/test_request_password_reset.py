from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from user_management_service.application.use_cases.request_password_reset import (
    RequestPasswordResetUseCase,
)
from user_management_service.domain.entities.role import Role
from user_management_service.domain.entities.user import User

pytestmark = pytest.mark.asyncio(loop_scope="session")


def make_domain_user(**overrides) -> User:
    defaults = dict(
        id=uuid4(),
        name="Alice",
        surname="Smith",
        username="alice",
        email="alice@example.com",
        password_hash="hashed:pw",
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


class TestRequestPasswordResetUseCase:
    async def test_publishes_message_when_user_exists(self):
        user = make_domain_user(email="alice@example.com")
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = user

        jwt_service = MagicMock()
        jwt_service.create_password_reset_token.return_value = "reset-jwt-token"

        publisher = AsyncMock()

        use_case = RequestPasswordResetUseCase(
            user_repo=user_repo,
            jwt_service=jwt_service,
            message_publisher=publisher,
            reset_password_base_url="http://localhost:3000/reset-password",
        )

        await use_case.execute("alice@example.com")

        jwt_service.create_password_reset_token.assert_called_once_with(user.id)
        publisher.publish_reset_password.assert_awaited_once()

        message = publisher.publish_reset_password.call_args.args[0]
        assert message.email == "alice@example.com"
        assert "reset-jwt-token" in message.body
        assert "http://localhost:3000/reset-password?token=reset-jwt-token" in message.body

    async def test_does_not_publish_when_user_not_found(self):
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = None

        jwt_service = MagicMock()
        publisher = AsyncMock()

        use_case = RequestPasswordResetUseCase(
            user_repo=user_repo,
            jwt_service=jwt_service,
            message_publisher=publisher,
            reset_password_base_url="http://localhost:3000/reset-password",
        )

        await use_case.execute("ghost@example.com")

        jwt_service.create_password_reset_token.assert_not_called()
        publisher.publish_reset_password.assert_not_awaited()

    async def test_message_subject_is_set(self):
        user = make_domain_user()
        user_repo = AsyncMock()
        user_repo.get_by_email.return_value = user

        jwt_service = MagicMock()
        jwt_service.create_password_reset_token.return_value = "tok"

        publisher = AsyncMock()

        use_case = RequestPasswordResetUseCase(
            user_repo=user_repo,
            jwt_service=jwt_service,
            message_publisher=publisher,
            reset_password_base_url="http://localhost:3000/reset-password",
        )

        await use_case.execute(user.email)

        message = publisher.publish_reset_password.call_args.args[0]
        assert message.subject == "Password reset request"
        assert message.published_at is not None
