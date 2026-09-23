from uuid import UUID

from user_management_service.application.interfaces.user_repository import (
    IUserRepository,
)
from user_management_service.domain.exceptions import UserNotFoundError


class DeleteUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID) -> None:
        success = await self.user_repo.delete(user_id)
        if not success:
            raise UserNotFoundError(str(user_id))
