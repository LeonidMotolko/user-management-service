from abc import ABC, abstractmethod

from user_management_service.domain.entities.group import Group


class IGroupRepository(ABC):
    @abstractmethod
    async def get_by_id(self, group_id: int) -> Group | None: ...
