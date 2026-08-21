from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.team.team_member import TeamMember


class TeamMemberRepositoryPort(BaseRepositoryPort[TeamMember]):
    @abstractmethod
    async def find_members_by_team_id(self, team_id: UUID) -> List[TeamMember]:
        pass

    @abstractmethod
    async def find_by_team_and_user(
        self, team_id: UUID, user_id: UUID
    ) -> Optional[TeamMember]:
        pass

    @abstractmethod
    async def exists_by_team_and_user(self, team_id: UUID, user_id: UUID) -> bool:
        pass

    @abstractmethod
    async def count_by_team(self, team_id: UUID) -> int:
        pass

    @abstractmethod
    async def count_pending_donations_by_team(self, team_id: UUID) -> int:
        pass

    @abstractmethod
    async def delete(self, team_member_id: UUID) -> int:
        pass
