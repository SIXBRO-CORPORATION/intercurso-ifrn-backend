from typing import List

from core.business.season.list_seasons_port import ListSeasonsPort
from core.context import Context
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.season.season import Season


class ListSeasonsAdapter(ListSeasonsPort):
    def __init__(self, season_repository: SeasonRepositoryPort):
        self.season_repository = season_repository

    async def execute(self, context: Context) -> List[Season]:
        status_filter = context.get_property("status", SeasonStatus)
        year_filter = context.get_property("year", int)

        if status_filter is not None:
            return await self.season_repository.find_by_status(status_filter)

        if year_filter is not None:
            return await self.season_repository.find_by_year(year_filter)

        return await self.season_repository.find_all()
