from core.business.season.get_active_season_port import GetActiveSeasonPort
from core.context import Context
from core.persistence.season.season_repository_port import SeasonRepositoryPort
from domain.exceptions.business_exception import BusinessException
from domain.season.season import Season


class GetActiveSeasonAdapter(GetActiveSeasonPort):
    def __init__(self, season_repository: SeasonRepositoryPort):
        self.season_repository = season_repository

    async def execute(self, context: Context) -> Season:
        season = await self.season_repository.find_active_season()

        if season is None:
            raise BusinessException("Nenhuma temporada ativa no momento")

        return season
