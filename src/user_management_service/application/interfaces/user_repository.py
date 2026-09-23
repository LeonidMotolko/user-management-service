from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from user_management_service.domain.entities.user import User

SortField = Literal["name", "surname", "username", "email", "created_at"]
OrderDirection = Literal["asc", "desc"]


@dataclass(frozen=True, slots=True)
class UserListFilter:
    page: int = 1
    limit: int = 30
    filter_by_name: str | None = None
    sort_by: SortField = "created_at"
    order_by: OrderDirection = "asc"
    group_id: int | None = None
    restrict_to_group: bool = False


class IUserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> User:
        """Add new user."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Get user by username."""

    @abstractmethod
    async def get_by_phone_number(self, phone_number: str) -> User | None:
        """Get user by phone number."""

    async def update(self, user: User) -> User:
        """Update user"""

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID."""

    @abstractmethod
    async def list_users(self, filters: UserListFilter) -> tuple[list[User], int]:
        """Return a page of users matching the filters, and the total count
        (total ignores pagination but respects name filter and group restriction)."""
