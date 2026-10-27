from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.messaging.device_token import DeviceToken


class DeviceTokenRepositoryPort(BaseRepositoryPort[DeviceToken]):
    @abstractmethod
    async def find_by_token(self, token: str) -> Optional[DeviceToken]:
        pass

    @abstractmethod
    async def find_active_by_user(self, user_id: UUID) -> List[DeviceToken]:
        pass

    @abstractmethod
    async def find_active_by_users(self, user_ids: List[UUID]) -> List[DeviceToken]:
        pass

    @abstractmethod
    async def deactivate_by_token(self, token: str) -> None:
        pass
