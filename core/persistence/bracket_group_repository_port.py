from abc import abstractmethod
from typing import List
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.bracket_group import BracketGroup


class BracketGroupRepositoryPort(BaseRepositoryPort[BracketGroup]):
    @abstractmethod
    async def find_by_bracket(self, bracket_id: UUID) -> List[BracketGroup]:
        pass

    @abstractmethod
    async def delete_by_bracket(self, bracket_id: UUID) -> int:
        pass