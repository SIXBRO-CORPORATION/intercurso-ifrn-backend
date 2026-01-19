from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.season_modality import SeasonModality


class SeasonModalityRepositoryPort(BaseRepositoryPort[SeasonModality]):
    @abstractmethod
    async def find_by_season(self, season_id: UUID) -> List[SeasonModality]:
        pass

    @abstractmethod
    async def find_by_season_and_modality(
        self, season_id: UUID, modality_id: UUID
    ) -> Optional[SeasonModality]:
        pass

    @abstractmethod
    async def exists_by_season_and_modality(
        self, season_id: UUID, modality_id: UUID
    ) -> bool:
        pass

    @abstractmethod
    async def delete_by_season(self, season_id: UUID) -> int:
        pass