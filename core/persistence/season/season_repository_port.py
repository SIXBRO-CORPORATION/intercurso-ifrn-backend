from abc import abstractmethod
from datetime import datetime
from typing import Optional, List

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.season.season import Season


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
    async def find_draft_ready_to_open(self, now: datetime) -> List[Season]:
        pass

    @abstractmethod
    async def find_open_with_registration_ended(self, now: datetime) -> List[Season]:
        pass

    @abstractmethod
    async def exists_active_season(self) -> bool:
        pass