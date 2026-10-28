from abc import ABC, abstractmethod

from domain.season.season import Season


class SeasonBroadcastPort(ABC):

    @abstractmethod
    async def registration_opened(self, season: Season) -> None:
        pass

    @abstractmethod
    async def registration_closed(self, season: Season) -> None:
        pass

    @abstractmethod
    async def registration_reopened(self, season: Season) -> None:
        pass

    @abstractmethod
    async def season_finished(self, season: Season) -> None:
        pass
