from abc import abstractmethod
from typing import List
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.match.match_set import MatchSet


class MatchSetRepositoryPort(BaseRepositoryPort[MatchSet]):
    @abstractmethod
    async def find_by_match(self, match_id: UUID) -> List[MatchSet]:
        pass

    @abstractmethod
    async def count_sets_won_by_team(self, match_id: UUID) -> dict:
        pass
