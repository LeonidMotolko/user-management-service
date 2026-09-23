from user_management_service.application.dto.user import (
    PaginatedUsersDTO,
    UserResponseDTO,
)
from user_management_service.application.interfaces.user_repository import (
    IUserRepository,
    UserListFilter,
)


class ListUsersUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, filters: UserListFilter) -> PaginatedUsersDTO:
        users, total = await self.user_repo.list_users(filters)
        return PaginatedUsersDTO(
            items=[UserResponseDTO.model_validate(u) for u in users],
            total=total,
            page=filters.page,
            limit=filters.limit,
        )
