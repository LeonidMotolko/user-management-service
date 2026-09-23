from uuid import uuid4

from user_management_service.application.dto.user import (
    CreateUserDTO,
    UserResponseDTO,
)
from user_management_service.application.interfaces.group_repository import (
    IGroupRepository,
)
from user_management_service.application.interfaces.password_hasher import (
    IPasswordHasher,
)
from user_management_service.application.interfaces.user_repository import (
    IUserRepository,
)
from user_management_service.domain.entities.user import User
from user_management_service.domain.exceptions import (
    GroupNotFoundError,
    UserAlreadyExistsError,
)


class CreateUserUseCase:
    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: IPasswordHasher,
        group_repository: IGroupRepository | None = None,
    ):
        self.user_repo = user_repository
        self.password_hasher = password_hasher
        self.group_repo = group_repository

    async def execute(self, dto: CreateUserDTO) -> UserResponseDTO:
        if await self.user_repo.get_by_email(dto.email):
            raise UserAlreadyExistsError("email", dto.email)

        if await self.user_repo.get_by_username(dto.username):
            raise UserAlreadyExistsError("username", dto.username)

        if dto.phone_number and await self.user_repo.get_by_phone_number(dto.phone_number):
            raise UserAlreadyExistsError("phone_number", dto.phone_number)

        group = None
        if dto.group_id:
            if not self.group_repo:
                raise ValueError("Group repository is not configured.")
            group = await self.group_repo.get_by_id(dto.group_id)
            if not group:
                raise GroupNotFoundError(dto.group_id)

        hashed_password = self.password_hasher.hash(dto.password)

        user = User(
            id=uuid4(),
            name=dto.name,
            surname=dto.surname,
            username=dto.username,
            email=dto.email,
            password_hash=hashed_password,
            role=dto.role,
            group=group,
            phone_number=dto.phone_number,
        )

        saved_user = await self.user_repo.add(user)
        return UserResponseDTO.model_validate(saved_user)
