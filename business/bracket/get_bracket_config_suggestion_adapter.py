from uuid import UUID

from business.bracket.engine.config_suggester import (
    resolve_configuration,
    validate_team_count_for_format,
)
from business.bracket.engine.draw_engine import next_power_of_two
from core.business.bracket.get_bracket_config_suggestion_port import (
    GetBracketConfigSuggestionPort,
)
from core.context import Context
from core.persistence.bracket_repository_port import BracketRepositoryPort
from core.persistence.season_modality_repository_port import (
    SeasonModalityRepositoryPort,
)
from core.persistence.season_repository_port import SeasonRepositoryPort
from core.persistence.team_repository_port import TeamRepositoryPort
from domain.enums.modality_format import ModalityFormat
from domain.enums.season_status import SeasonStatus
from domain.exceptions.business_exception import BusinessException


class GetBracketConfigSuggestionAdapter(GetBracketConfigSuggestionPort):
    def __init__(
        self,
        season_repository: SeasonRepositoryPort,
        season_modality_repository: SeasonModalityRepositoryPort,
        team_repository: TeamRepositoryPort,
        bracket_repository: BracketRepositoryPort,
    ):
        self.season_repository = season_repository
        self.season_modality_repository = season_modality_repository
        self.team_repository = team_repository
        self.bracket_repository = bracket_repository

    async def execute(self, context: Context) -> dict:
        modality_id = context.get_property("modality_id", UUID)
        modality_format = context.get_property("format", ModalityFormat)

        if modality_id is None:
            raise BusinessException("Modalidade é obrigatória")
        if modality_format is None:
            raise BusinessException("Formato do chaveamento é obrigatório")

        active_season = await self.season_repository.find_active_season()
        if active_season is None:
            raise BusinessException("Não há uma temporada ativa no momento")

        if active_season.status == SeasonStatus.REGISTRATION_OPEN:
            raise BusinessException(
                "Período de inscrições ainda está aberto. Aguarde o encerramento."
            )
        if active_season.status not in (
            SeasonStatus.REGISTRATION_CLOSED,
            SeasonStatus.IN_PROGRESS,
        ):
            raise BusinessException(
                "Temporada precisa estar com inscrições encerradas ou em "
                "andamento para configurar um chaveamento"
            )

        modality_in_season = (
            await self.season_modality_repository.exists_by_season_and_modality(
                active_season.id, modality_id
            )
        )
        if not modality_in_season:
            raise BusinessException(
                "Modalidade informada não faz parte da temporada ativa"
            )

        if await self.bracket_repository.exists_active_bracket_for_modality(
            active_season.id, modality_id
        ):
            raise BusinessException(
                "Já existe um chaveamento ativo criado para essa modalidade"
            )

        approved_teams = (
            await self.team_repository.find_approved_teams_by_season_and_modality(
                active_season.id, modality_id
            )
        )
        team_count = len(approved_teams)

        validate_team_count_for_format(modality_format, team_count)

        resolved_config = resolve_configuration(modality_format, team_count, None)

        context.put_property("team_count", team_count)
        if modality_format == ModalityFormat.KNOCKOUT:
            byes_estimated = next_power_of_two(team_count) - team_count
        else:
            byes_estimated = 0
        context.put_property("byes_estimated", byes_estimated)

        return resolved_config
