from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from user_management_service.application.dto.user import (
    UpdateUserDTO,
    UserResponseDTO,
)
from user_management_service.application.use_cases.delete_user import (
    DeleteUserUseCase,
)
from user_management_service.application.use_cases.get_user import (
    GetUserUseCase,
)
from user_management_service.application.use_cases.update_user import (
    UpdateUserUseCase,
)
from user_management_service.domain.entities.role import Role
from user_management_service.domain.entities.user import User
from user_management_service.domain.exceptions import UserNotFoundError
from user_management_service.presentation.api.v1.dependencies import (
    get_current_user,
    get_delete_user_use_case,
    get_get_user_use_case,
    get_update_user_use_case,
    require_admin_or_same_group,
    require_roles,
)

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me", response_model=UserResponseDTO)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[GetUserUseCase, Depends(get_get_user_use_case)],
):
    return await use_case.execute(current_user.id)


@router.patch("/me", response_model=UserResponseDTO)
async def update_me(
    dto: UpdateUserDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[UpdateUserUseCase, Depends(get_update_user_use_case)],
):
    return await use_case.execute(current_user.id, dto)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[DeleteUserUseCase, Depends(get_delete_user_use_case)],
):
    await use_case.execute(current_user.id)


@router.get(
    "/{user_id}",
    response_model=UserResponseDTO,
    dependencies=[Depends(require_admin_or_same_group)],
)
async def get_user(
    user_id: UUID,
    use_case: Annotated[GetUserUseCase, Depends(get_get_user_use_case)],
):
    try:
        return await use_case.execute(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{user_id}",
    response_model=UserResponseDTO,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
async def update_user(
    user_id: UUID,
    dto: UpdateUserDTO,
    use_case: Annotated[UpdateUserUseCase, Depends(get_update_user_use_case)],
):
    try:
        return await use_case.execute(user_id, dto)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
