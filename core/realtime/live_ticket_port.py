
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


class InvalidLiveTicketError(Exception):
    pass


class LiveTicketPort(ABC):
    @abstractmethod
    def issue_ticket(self, user_id: Optional[UUID], channel: str) -> str:
        """user_id=None emite um ticket anônimo (ADR 0004)."""

    @abstractmethod
    def verify_ticket(self, ticket: str, channel: str) -> Optional[UUID]:
        """Retorna None quando o ticket é anônimo."""
