from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from user_management_service.domain.entities.group import Group
from user_management_service.domain.entities.role import Role


@dataclass
class User:
    id: UUID
    name: str
    surname: str
    username: str
    password_hash: str
    email: str
    role: Role
    phone_number: Optional[str] = None
    group: Optional[Group] = None
    image_s3_path: Optional[str] = None
    is_blocked: bool = False
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
