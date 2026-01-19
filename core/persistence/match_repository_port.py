from abc import abstractmethod
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.enums.match_status import MatchStatus
from domain.match import Match


class MatchRepositoryPort(BaseRepositoryPort[Match]):
    @abstractmethod
    async def find_by_bracket(self, bracket_id: UUID) -> List[Match]:
        pass

    @abstractmethod
    async def find_by_team(self, team_id: UUID) -> List[Match]:
        pass

    @abstractmethod
    async def find_by_status(self, status: MatchStatus) -> List[Match]:
        pass

    @abstractmethod
    async def find_in_progress_matches(self) -> List[Match]:
        pass

    @abstractmethod
    async def find_scheduled_by_date(
        self, start_date: datetime, end_date: datetime
    ) -> List[Match]:
        pass

    @abstractmethod
    async def find_by_bracket_group(self, bracket_group_id: UUID) -> List[Match]:
        pass

    @abstractmethod
    async def delete_by_bracket(self, bracket_id: UUID) -> int:
        pass

    @abstractmethod
    async def find_tbd_matches_by_bracket(self, bracket_id: UUID) -> List[Match]:
        pass