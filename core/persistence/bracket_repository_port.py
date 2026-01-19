from abc import abstractmethod
from typing import Optional, List
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.bracket import Bracket
from domain.enums.bracket_status import BracketStatus


class BracketRepositoryPort(BaseRepositoryPort[Bracket]):
    @abstractmethod
    async def find_by_season_and_modality(
        self, season_id: UUID, modality_id: UUID
    ) -> Optional[Bracket]:
        pass

    @abstractmethod
    async def find_by_season(self, season_id: UUID) -> List[Bracket]:
        pass

    @abstractmethod
    async def find_by_status(self, status: BracketStatus) -> List[Bracket]:
        pass

    @abstractmethod
    async def exists_active_bracket_for_modality(
        self, season_id: UUID, modality_id: UUID
    ) -> bool:
        pass

    @abstractmethod
    async def find_active_by_season_and_modality(
        self, season_id: UUID, modality_id: UUID
    ) -> Optional[Bracket]:
        pass