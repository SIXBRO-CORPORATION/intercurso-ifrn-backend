from abc import abstractmethod
from typing import List
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.bracket_group_team import BracketGroupTeam


class BracketGroupTeamRepositoryPort(BaseRepositoryPort[BracketGroupTeam]):
    @abstractmethod
    async def find_by_group(self, bracket_group_id: UUID) -> List[BracketGroupTeam]:
        pass

    @abstractmethod
    async def find_by_bracket_group_and_team(
        self, bracket_group_id: UUID, team_id: UUID
    ) -> BracketGroupTeam:
        pass

    @abstractmethod
    async def delete_by_bracket(self, bracket_id: UUID) -> int:
        pass