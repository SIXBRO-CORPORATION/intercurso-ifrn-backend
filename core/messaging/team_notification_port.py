from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from domain.team.team import Team


class TeamNotificationPort(ABC):

    @abstractmethod
    async def team_approved(self, team: Team, member_user_ids: Sequence[UUID]) -> None:
        pass

    @abstractmethod
    async def team_rejected(
        self, team: Team, member_user_ids: Sequence[UUID], reason: str
    ) -> None:
        pass

    @abstractmethod
    async def member_removed(self, team: Team, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def captain_selected(self, team: Team, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def donation_confirmed(self, team: Team, user_id: UUID) -> None:
        pass

    @abstractmethod
    async def member_joined(self, team: Team, member_name: str) -> None:
        pass

    @abstractmethod
    async def member_left(self, team: Team, member_name: str) -> None:
        pass
