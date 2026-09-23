from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from user_management_service.application.dto.auth import (
    LoginDTO,
    RefreshTokenDTO,
    ResetPasswordRequestDTO,
    TokenResponseDTO,
)
from user_management_service.application.dto.user import SignupDTO
from user_management_service.application.use_cases.create_user import (
    CreateUserUseCase,
)
from user_management_service.application.use_cases.login_user import (
    InvalidCredentialsError,
    LoginUserUseCase,
)
from user_management_service.application.use_cases.refresh_token import (
    InvalidTokenError,
    RefreshTokenUseCase,
)
from user_management_service.application.use_cases.request_password_reset import (
    RequestPasswordResetUseCase,
)
from user_management_service.domain.entities.user import User
from user_management_service.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from user_management_service.presentation.api.v1.dependencies import (
    get_create_user_use_case,
    get_current_user,
    get_login_use_case,
    get_refresh_token_use_case,
    get_request_password_reset_use_case,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    dto: SignupDTO,
    use_case: Annotated[CreateUserUseCase, Depends(get_create_user_use_case)],
):
    try:
        await use_case.execute(dto.to_create_user_dto())
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    return {"detail": "User registered successfully"}


@router.post("/login", response_model=TokenResponseDTO)
async def login(
    dto: LoginDTO,
    use_case: Annotated[LoginUserUseCase, Depends(get_login_use_case)],
):
    try:
        return await use_case.execute(dto)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.post("/refresh-token", response_model=TokenResponseDTO)
async def refresh_token(
    dto: RefreshTokenDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[RefreshTokenUseCase, Depends(get_refresh_token_use_case)],
):
    try:
        return await use_case.execute(dto, current_user_id=current_user.id)
    except (InvalidTokenError, UserNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e


@router.post("/reset-password", status_code=status.HTTP_202_ACCEPTED)
async def reset_password(
    dto: ResetPasswordRequestDTO,
    use_case: Annotated[RequestPasswordResetUseCase, Depends(get_request_password_reset_use_case)],
):
    await use_case.execute(dto.email)
    return {"detail": "If this email exists, a password reset link has been sent."}
