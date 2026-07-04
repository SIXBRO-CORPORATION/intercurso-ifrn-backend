from uuid import UUID

from core.business.season.get_season_details_port import GetSeasonDetailsPort
from core.context import Context
from core.persistence.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.season_repository_port import SeasonRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from domain.enums.season_status import SeasonStatus
from domain.enums.team_status import TeamStatus
from domain.exceptions.business_exception import BusinessException
from domain.season import Season

_AVAILABLE_ACTIONS_BY_STATUS = {
    SeasonStatus.DRAFT: ["edit_registration_dates", "postpone_opening"],
    SeasonStatus.REGISTRATION_OPEN: [
        "edit_registration_end_date",
        "close_registration_early",
    ],
    SeasonStatus.REGISTRATION_CLOSED: ["reopen_registration"],
    SeasonStatus.IN_PROGRESS: [],
    SeasonStatus.FINISHED: [],
}


class GetSeasonDetailsAdapter(GetSeasonDetailsPort):
    def __init__(
        self,
        season_repository: SeasonRepositoryPort,
        season_modality_repository: SeasonModalityRepositoryPort,
        team_repository: TeamRepositoryPort,
    ):
        self.season_repository = season_repository
        self.season_modality_repository = season_modality_repository
        self.team_repository = team_repository

    async def execute(self, context: Context) -> Season:
        season_id = context.get_property("season_id", UUID)

        if season_id is None:
            raise BusinessException("Identificador da temporada é obrigatório")

        season = await self.season_repository.get(season_id)
        if season is None:
            raise BusinessException("Temporada não encontrada")

        season_modalities = await self.season_modality_repository.find_by_season(
            season_id
        )
        teams = await self.team_repository.find_by_season_id(season_id)

        total_teams_created = len(teams)
        total_teams_submitted = sum(
            1 for team in teams if team.status != TeamStatus.DRAFT
        )
        total_teams_approved = sum(
            1 for team in teams if team.status == TeamStatus.APPROVED
        )

        context.put_property("season_modalities", season_modalities)
        context.put_property("total_teams_created", total_teams_created)
        context.put_property("total_teams_submitted", total_teams_submitted)
        context.put_property("total_teams_approved", total_teams_approved)
        context.put_property(
            "available_actions",
            _AVAILABLE_ACTIONS_BY_STATUS.get(season.status, []),
        )

        return season
