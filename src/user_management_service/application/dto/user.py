from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from user_management_service.domain.entities.role import Role


class GroupDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime | None = None


class CreateUserDTO(BaseModel):
    name: str
    surname: str
    username: str
    email: EmailStr
    password: str
    role: Role = Role.USER
    group_id: int | None = None
    phone_number: str | None = None


class SignupDTO(BaseModel):
    name: str
    surname: str
    username: str
    email: EmailStr
    password: str
    phone_number: str | None = None

    def to_create_user_dto(self) -> "CreateUserDTO":
        return CreateUserDTO(
            name=self.name,
            surname=self.surname,
            username=self.username,
            email=self.email,
            password=self.password,
            phone_number=self.phone_number,
            role=Role.USER,
        )


class UpdateUserDTO(BaseModel):
    name: str | None = None
    surname: str | None = None
    phone_number: str | None = None
    image_s3_path: str | None = None



class UserResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    surname: str
    username: str
    email: str
    role: Role
    group: GroupDTO | None = None
    image_s3_path: str | None = None
    is_blocked: bool
    created_at: datetime | None = None


class PaginatedUsersDTO(BaseModel):
    items: list[UserResponseDTO]
    total: int
    page: int
    limit: int
