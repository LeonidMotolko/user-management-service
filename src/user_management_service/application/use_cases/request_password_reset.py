from datetime import UTC, datetime

from user_management_service.application.interfaces.message_publisher import (
    IMessagePublisher,
    ResetPasswordMessage,
)
from user_management_service.application.interfaces.user_repository import (
    IUserRepository,
)
from user_management_service.infrastructure.security.jwt_service import JWTService


class RequestPasswordResetUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        jwt_service: JWTService,
        message_publisher: IMessagePublisher,
        reset_password_base_url: str,
    ):
        self.user_repo = user_repo
        self.jwt_service = jwt_service
        self.message_publisher = message_publisher
        self.reset_password_base_url = reset_password_base_url

    async def execute(self, email: str) -> None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return

        token = self.jwt_service.create_password_reset_token(user.id)
        reset_link = f"{self.reset_password_base_url}?token={token}"

        message = ResetPasswordMessage(
            email=user.email,
            subject="Password reset request",
            body=(
                f"Hi {user.name},\n\n"
                f"We received a request to reset your password. "
                f"Click the link below to set a new one (valid for 30 minutes):\n\n"
                f"{reset_link}\n\n"
                f"If you didn't request this, you can safely ignore this email."
            ),
            published_at=datetime.now(UTC),
        )
        await self.message_publisher.publish_reset_password(message)
