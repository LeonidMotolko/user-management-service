from uuid import UUID

from user_management_service.application.dto.user import UpdateUserDTO, UserResponseDTO
from user_management_service.application.interfaces.user_repository import (
    IUserRepository,
)
from user_management_service.domain.exceptions import UserNotFoundError


class UpdateUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID, dto: UpdateUserDTO) -> UserResponseDTO:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(str(user_id))

        if dto.name is not None:
            user.name = dto.name
        if dto.surname is not None:
            user.surname = dto.surname
        if dto.phone_number is not None:
            user.phone_number = dto.phone_number

        updated_user = await self.user_repo.update(user)
        return UserResponseDTO.model_validate(updated_user)
