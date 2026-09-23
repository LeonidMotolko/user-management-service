from uuid import uuid4

from user_management_service.application.dto.auth import LoginDTO, TokenResponseDTO
from user_management_service.application.interfaces.password_hasher import IPasswordHasher
from user_management_service.application.interfaces.user_repository import IUserRepository
from user_management_service.domain.exceptions import DomainError
from user_management_service.infrastructure.security.jwt_service import JWTService


class InvalidCredentialsError(DomainError):
    def __init__(self):
        super().__init__("Invalid login credentials.")


class LoginUserUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        password_hasher: IPasswordHasher,
        jwt_service: JWTService,
    ):
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.jwt_service = jwt_service

    async def execute(self, dto: LoginDTO) -> TokenResponseDTO:
        # Поиск пользователя по email или username
        user = await self.user_repo.get_by_email(dto.login)
        if not user:
            user = await self.user_repo.get_by_username(dto.login)

        if not user or not self.password_hasher.verify(dto.password, user.password_hash):
            raise InvalidCredentialsError()

        jti = str(uuid4())
        access_token = self.jwt_service.create_access_token(user.id, user.role.value)
        refresh_token = self.jwt_service.create_refresh_token(user.id, jti)

        return TokenResponseDTO(access_token=access_token, refresh_token=refresh_token)
