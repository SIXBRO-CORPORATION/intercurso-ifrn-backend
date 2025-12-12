from abc import abstractmethod
from typing import List
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.enums.team_status import TeamStatus
from domain.team import Team


class TeamRepositoryPort(BaseRepositoryPort[Team]):

    @abstractmethod
    async def exists_by_id(self, team_id: UUID) -> bool:
        pass

    @abstractmethod
    async def find_teams_by_matricula(self, matricula: int) -> List[Team]:
        pass

    @abstractmethod
    async def find_teams_by_user_id(self, user_id: UUID) -> List[Team]:
        pass

    @abstractmethod
    async def find_teams_by_status(self, status: TeamStatus) -> List[Team]:
        pass

