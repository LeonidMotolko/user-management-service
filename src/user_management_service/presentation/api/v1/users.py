from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from user_management_service.application.dto.user import PaginatedUsersDTO
from user_management_service.application.interfaces.user_repository import (
    OrderDirection,
    SortField,
    UserListFilter,
)
from user_management_service.application.use_cases.list_users import (
    ListUsersUseCase,
)
from user_management_service.domain.entities.role import Role
from user_management_service.domain.entities.user import User
from user_management_service.presentation.api.v1.dependencies import (
    get_list_users_use_case,
    require_roles,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedUsersDTO)
async def list_users(
    current_user: Annotated[User, Depends(require_roles(Role.ADMIN, Role.MODERATOR))],
    use_case: Annotated[ListUsersUseCase, Depends(get_list_users_use_case)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    filter_by_name: str | None = None,
    sort_by: SortField = "created_at",
    order_by: OrderDirection = "asc",
):
    restrict_to_group = current_user.role == Role.MODERATOR
    if restrict_to_group and not current_user.group:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator is not assigned to a group",
        )

    filters = UserListFilter(
        page=page,
        limit=limit,
        filter_by_name=filter_by_name,
        sort_by=sort_by,
        order_by=order_by,
        group_id=current_user.group.id if restrict_to_group and current_user.group else None,
        restrict_to_group=restrict_to_group,
    )
    return await use_case.execute(filters)
