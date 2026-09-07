from uuid import UUID

from user_management_service.application.dto.user import UserResponseDTO
from user_management_service.application.interfaces.user_repository import (
    IUserRepository,
)
from user_management_service.domain.exceptions import UserNotFoundError


class BlockUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID, is_blocked: bool = True) -> UserResponseDTO:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        user.is_blocked = is_blocked
        updated_user = await self.user_repo.update(user)
        return UserResponseDTO.model_validate(updated_user)
