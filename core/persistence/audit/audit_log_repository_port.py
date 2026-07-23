from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from domain.audit_log import AuditLog


class AuditLogRepositoryPort(ABC):
    @abstractmethod
    async def save(self, audit_log: AuditLog) -> AuditLog:
        pass

    @abstractmethod
    async def find_all(self) -> List[AuditLog]:
        pass

    @abstractmethod
    async def find_by_actor_id(self, actor_id: UUID) -> List[AuditLog]:
        pass