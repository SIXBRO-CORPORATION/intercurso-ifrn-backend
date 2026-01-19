from abc import abstractmethod
from typing import Optional, List

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.season import Season


class SeasonRepositoryPort(BaseRepositoryPort[Season]):
    @abstractmethod
    async def find_active_season(self) -> Optional[Season]:
        pass

    @abstractmethod
    async def find_by_status(self, status: SeasonStatus) -> List[Season]:
        pass

    @abstractmethod
    async def find_by_year(self, year: int) -> List[Season]:
        pass

    @abstractmethod
    async def exists_active_season(self) -> bool:
        pass