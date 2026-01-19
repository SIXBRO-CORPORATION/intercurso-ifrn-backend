from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from core.persistence.commons.base_repository_port import BaseRepositoryPort
from domain.enums.event_type import EventType
from domain.match_event import MatchEvent


class MatchEventRepositoryPort(BaseRepositoryPort[MatchEvent]):
    @abstractmethod
    async def find_by_match(self, match_id: UUID) -> List[MatchEvent]:
        pass

    @abstractmethod
    async def find_by_match_and_type(
        self, match_id: UUID, event_type: EventType
    ) -> List[MatchEvent]:
        pass

    @abstractmethod
    async def find_by_player(self, player_id: UUID) -> List[MatchEvent]:
        pass

    @abstractmethod
    async def find_active_by_match(self, match_id: UUID) -> List[MatchEvent]:
        pass

    @abstractmethod
    async def find_last_event_by_match(self, match_id: UUID) -> Optional[MatchEvent]:
        pass

    @abstractmethod
    async def soft_delete_event(self, event_id: UUID) -> bool:
        pass