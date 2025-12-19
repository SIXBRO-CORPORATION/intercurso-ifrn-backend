from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.team import Team
from domain.team_member import TeamMember
from domain.user import User


class TeamMemberRepositoryPort(BaseRepositoryPort[TeamMember]):
    @abstractmethod
    async def find_members_by_team_id(self, team_id: UUID) -> List[TeamMember]:
        pass

    @abstractmethod
    async def find_member_by_matricula_and_team_id(
        self, matricula: int, team_id: UUID
    ) -> Optional[TeamMember]:
        pass
