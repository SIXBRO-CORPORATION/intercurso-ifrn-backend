from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.team_member import TeamMember


class TeamMemberRepositoryPort(BaseRepositoryPort[TeamMember]):
    @abstractmethod
    async def find_members_by_team_id(self, team_id: UUID) -> List[TeamMember]:
        pass
