from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from user_management_service.application.dto.user import (
    CreateUserDTO,
    UpdateUserDTO,
    UserResponseDTO,
)
from user_management_service.application.use_cases.block_user import (
    BlockUserUseCase,
)
from user_management_service.application.use_cases.create_user import (
    CreateUserUseCase,
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
from user_management_service.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from user_management_service.presentation.api.v1.dependencies import (
    get_block_user_use_case,
    get_create_user_use_case,
    get_delete_user_use_case,
    get_get_user_use_case,
    get_update_user_use_case,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_user(
    dto: CreateUserDTO,
    use_case: Annotated[CreateUserUseCase, Depends(get_create_user_use_case)],
):
    try:
        return await use_case.execute(dto)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{user_id}", response_model=UserResponseDTO)
async def get_user(
    user_id: UUID,
    use_case: Annotated[GetUserUseCase, Depends(get_get_user_use_case)],
):
    try:
        return await use_case.execute(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{user_id}", response_model=UserResponseDTO)
async def update_user(
    user_id: UUID,
    dto: UpdateUserDTO,
    use_case: Annotated[UpdateUserUseCase, Depends(get_update_user_use_case)],
):
    try:
        return await use_case.execute(user_id, dto)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    use_case: Annotated[DeleteUserUseCase, Depends(get_delete_user_use_case)],
):
    try:
        await use_case.execute(user_id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{user_id}/block", response_model=UserResponseDTO)
async def block_user(
    user_id: UUID,
    is_blocked: bool,
    use_case: Annotated[BlockUserUseCase, Depends(get_block_user_use_case)],
):
    try:
        return await use_case.execute(user_id, is_blocked=is_blocked)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
