from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from user_management_service.domain.entities.group import Group
from user_management_service.domain.entities.role import Role


class User(BaseModel):
    id: UUID
    name: str
    surname: str
    username: str
    password_hash: str
    email: str
    role: Role
    phone_number: str | None = None
    group: Group | None = None
    image_s3_path: str | None = None
    is_blocked: bool = False
    created_at: datetime | None = None
    modified_at: datetime | None = None
