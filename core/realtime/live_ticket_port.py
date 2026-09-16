
from abc import ABC, abstractmethod
from uuid import UUID


class InvalidLiveTicketError(Exception):
    pass


class LiveTicketPort(ABC):
    @abstractmethod
    def issue_ticket(self, user_id: UUID, channel: str) -> str:
        pass

    @abstractmethod
    def verify_ticket(self, ticket: str, channel: str) -> UUID:
        pass
