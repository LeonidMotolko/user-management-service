from abc import ABC, abstractmethod
from uuid import UUID

from user_management_service.domain.entities.user import User


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
    async def update(self, user: User) -> User:
        """Update user"""

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Delete user by ID."""
